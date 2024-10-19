from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import hashlib

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DB_FILE = "posts.db"

# Инициализировать БД
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            operation TEXT NOT NULL,                   
            user_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Захэшировать пароль
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Получить куки
def get_cookie(request: Request, key: str):
    return request.cookies.get(key)

# Установить куки
def set_cookie(response: Response, key: str, value: str, max_age: int = 3600):
    print(f"Cookie set: {key} = {value}")
    response.set_cookie(key=key, value=value, httponly=True, max_age=max_age, secure=True, samesite='none')
    return True

# Проверить пользователя в БД
def verify_user(username: str, password: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()
    conn.close()
    return user[0] if user else None

# Получить текущего пользователя по cookie
def get_current_user(request: Request):
    user_id = get_cookie(request, "user_id")
    print(f"get_current_user --------: {user_id}")
    if not user_id:
        return None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user[0]

# Получить все посты
def get_posts():
    print('get_posts')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, user_id FROM posts")
    posts = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "content": row[2], "user_id": row[3]} for row in posts]

# Получить данные поста
def get_post(post_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content, user_id FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    if post:
        return {"id": post[0], "title": post[1], "content": post[2], "user_id": post[3]}
    return None

# Создание поста
def create_post(title, content, user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Получаем user_id пользователя
    cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
    user_id = cursor.fetchone()

    if not user_id:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Сохраняем пост в базу данных с user_id
    cursor.execute("INSERT INTO blog (title, content, user_id) VALUES (?, ?, ?)", (title, content, user_id[0]))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Логируем операцию создания поста
    log_operation(post_id, "create", user)

# Обновление поста
def update_blog_post(post_id, title, content, user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Получаем user_id пользователя
    cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
    user_id = cursor.fetchone()

    if not user_id:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # Обновляем пост, принадлежащий этому пользователю
    cursor.execute("UPDATE blog SET title = ?, content = ? WHERE id = ? AND user_id = ?", (title, content, post_id, user_id[0]))
    conn.commit()
    conn.close()

def delete_blog_post(post_id, user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM blog WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    log_operation(post_id, "delete", user)

def log_operation(post_id, operation, user):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (post_id, operation, user) VALUES (?, ?, ?)", (post_id, operation, user))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT post_id, operation, user, timestamp FROM history ORDER BY timestamp DESC")
    history = cursor.fetchall()
    conn.close()
    return [{"post_id": row[0], "operation": row[1], "user": row[2], "timestamp": row[3]} for row in history]

def clear_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()

# Стартовая страница
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user_id = get_current_user(request)
    print(f"User ID from cookie: {user_id}")
    #user_id = get_cookie(request, "user_id")
    posts = get_posts()
    return templates.TemplateResponse("index.html", {"request": request, "user": user_id, "posts": posts})

# Регистрация и авторизация
@app.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/auth/register")
async def register(username: str = Form(...), password: str = Form(...)): # request: Request,
    hashed_password = hash_password(password)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")
    conn.close()
    return RedirectResponse("/auth/login", status_code=303)

@app.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/auth/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)): # request: Request, 
    user_id = verify_user(username, password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Проверим, что пользователь найден и хеш пароля правильный
    print(f"User found: {user_id}, setting cookie")

    # Устанавливаем cookie с user_id
    set_cookie(response, "user_id", str(user_id))

    return RedirectResponse("/", status_code=303) # здесь не работает

@app.get("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("user_id")
    return RedirectResponse("/auth/login", status_code=303)

# Записи
@app.get("/post/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    user = get_current_user(request)
    return templates.TemplateResponse("post.html", {"request": request, "post": post, "user": user})

@app.get("/create_post", response_class=HTMLResponse)
async def create_post_form(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("create_post.html", {"request": request, "user": user})

@app.post("/create_post")
async def create_post(request: Request, title: str = Form(...), content: str = Form(...)):
    user = get_current_user(request)
    create_post(title, content, user)
    return RedirectResponse("/", status_code=303)

@app.get("/edit_post/{post_id}", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int):
    user = get_current_user(request)
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("edit_post.html", {"request": request, "user": user, "post": post})

@app.post("/edit_post/{post_id}")
async def edit_post(request: Request, post_id: int, title: str = Form(...), content: str = Form(...)):
    user = get_current_user(request)
    update_blog_post(post_id, title, content, user)
    return RedirectResponse("/", status_code=303)

@app.post("/delete_post/{post_id}")
async def delete_post(request: Request, post_id: int):
    user = get_current_user(request)
    delete_blog_post(post_id, user)
    return RedirectResponse("/", status_code=303)

# История операций
@app.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    history_data = get_history()
    return templates.TemplateResponse("history.html", {"request": request, "history": history_data})
    # user = get_current_user(request)
    # return templates.TemplateResponse("history.html", {"request": request, "history": history_data, "user": user})

@app.post("/history/clear")
async def clear_history_route(request: Request):
    clear_history()
    return RedirectResponse("/history", status_code=303)