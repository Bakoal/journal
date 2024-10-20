from db.models import User, Post, History
from db.init import SessionLocal
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
import hashlib, base64, hmac, json, time


# JWT
SECRET_KEY = "mysecretkey"  # Секретный ключ для подписи токенов
ALGORITHM = "HS256"  # Алгоритм шифрования

# Функция для генерации JWT токена
def create_jwt_token(data: dict, expires_in: int = 3600):
    # Заголовок
    header = {"alg": ALGORITHM, "typ": "JWT"}
    
    # Полезная нагрузка (payload) с данными и временем истечения
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in
    
    # Кодируем заголовок и полезную нагрузку в Base64
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    # Подписываем токен с помощью HMAC и SHA256
    signature = hmac.new(SECRET_KEY.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

# Функция для проверки JWT токена
def verify_jwt_token(token: str):
    try:
        # Разбиваем токен на три части: заголовок, полезная нагрузка и подпись
        header_b64, payload_b64, signature_b64 = token.split(".")
        
        # Проверяем подпись
        signature_check = hmac.new(SECRET_KEY.encode(), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
        signature_check_b64 = base64.urlsafe_b64encode(signature_check).decode().rstrip("=")
        
        if signature_check_b64 != signature_b64:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token signature")
        
        # Декодируем полезную нагрузку
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "===").decode())
        
        # Проверяем, не истек ли токен
        if time.time() > payload["exp"]:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        
        return payload  # Возвращаем полезную нагрузку
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Функция для получения текущего пользователя по токену
def get_current_user_jwt(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return verify_jwt_token(token)

# Функция для хэширования паролей
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def set_cookie(response: Response, key: str, value: str, max_age: int = 3600):
    response.set_cookie(
        key=key, 
        value=value, 
        httponly=True, 
        max_age=max_age, 
        secure=False, # True для HTTPS, False для HTTP (во время разработки)
        samesite='none' # 'lax' или 'strict' для большей безопасности, 'none' для использования на нескольких доменах
    )
    return True

# Функции для работы с базой данных
def get_current_user(request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()
    return user.username if user else None

def create_user(email: str, username: str, password: str):
    hashed_password = hash_password(password)
    session = SessionLocal()
    try:
        new_user = User(email=email, username=username, password=hashed_password)
        session.add(new_user)
        session.commit()
    except:
        session.rollback()
        # return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "User already exists"})
        raise HTTPException(status_code=400, detail="User already exists")
    finally:
        session.close()

def verify_user(username: str, password: str):
    session = SessionLocal()
    hashed_password = hash_password(password)
    user = session.query(User).filter_by(username=username, password=hashed_password).first()
    session.close()
    return user.id if user else None

def get_posts():
    session = SessionLocal()
    posts = session.query(Post).all()
    session.close()
    return [{"id": post.id, "title": post.title, "content": post.content, "user_id": post.user_id} for post in posts]

def get_post(post_id: int):
    session = SessionLocal()
    post = session.query(Post).filter_by(id=post_id).first()
    session.close()
    if post:
        return {"id": post.id, "title": post.title, "content": post.content, "user_id": post.user_id}
    return None

def create_new_post(title: str, content: str, username: str):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="User not found")
    new_post = Post(title=title, content=content, user_id=user.id)
    session.add(new_post)
    session.commit()
    log_operation(session, new_post.id, "create", user.id)
    session.close()

def update_blog_post(post_id: int, title: str, content: str, username: str):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="User not found")
    post = session.query(Post).filter_by(id=post_id, user_id=user.id).first()
    if post:
        post.title = title
        post.content = content
        session.commit()
    session.close()

def delete_blog_post(post_id: int, username: str):
    session = SessionLocal()
    user = session.query(User).filter_by(username=username).first()
    if user:
        session.query(Post).filter_by(id=post_id, user_id=user.id).delete()
        log_operation(session, post_id, "delete", user.id)
        session.commit()
    session.close()

def log_operation(session, post_id: int, operation: str, user_id: int):
    new_history = History(post_id=post_id, operation=operation, user_id=user_id)
    session.add(new_history)
    session.commit()

def get_history():
    session = SessionLocal()
    history = session.query(History).order_by(History.timestamp.desc()).all()
    session.close()
    return [{"post_id": h.post_id, "operation": h.operation, "user_id": h.user_id, "timestamp": h.timestamp} for h in history]

def clear_history():
    session = SessionLocal()
    session.query(History).delete()
    session.commit()
    session.close()
