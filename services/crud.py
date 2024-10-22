from db.models import User, Post, History
from db.init import SessionLocal
from fastapi import HTTPException, Response, status
from sqlalchemy.orm import Session
from services.schemas import UserCreate, UserLogin
import hashlib
from datetime import timedelta


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

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_user(user_data: UserLogin, db: Session):
    user = db.query(User).filter(User.username == user_data.username).first()
    if user is None:
        return None, "Неверная электронная почта или пароль"
    hashed_password = hash_password(user_data.password)
    if user.password != hashed_password:
        return None, "Неверная электронная почта или пароль" 
    return user, None

def get_current_user(request):
    username = request.cookies.get("username")
    if not username:
        return None
    return username

def create_user(user_data: UserCreate, db: Session):
    user_exists = db.query(User).filter((User.email == user_data.email) | (User.username == user_data.username)).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Пользователь с таким email или username уже существует")
    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, username=user_data.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    #log_operation(session=db, post_id=None, operation="register", user_id=new_user.id)
    return new_user

def get_posts(db: Session):
    posts = db.query(Post).all()
    return [{"id": post.id, "title": post.title, "content": post.content, "user_id": post.user_id} for post in posts]

def get_post(post_id: int, db: Session):
    post = db.query(Post).filter_by(id=post_id).first()
    if post:
        return {"id": post.id, "title": post.title, "content": post.content, "user_id": post.user_id}
    return None

def create_new_post(title: str, content: str, username: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    new_post = Post(
        title=title,
        content=content,
        user_id=user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    log_operation(db, new_post.id, "create", user.id)
    return new_post

def update_blog_post(post_id: int, title: str, content: str, username: str, db: Session):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.user.username != username:
        raise HTTPException(status_code=403, detail="У вас нет разрешения на удаление этого поста")
    post.title = title
    post.content = content
    db.commit()
    db.refresh(post)
    return post

def delete_blog_post(post_id: int, username: str, db: Session):
    #user = db.query(User).filter_by(username=username).first()
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.user.username != username:
        raise HTTPException(status_code=403, detail="У вас нет разрешения на удаление этого поста")
    #if user:
    #    db.query(Post).filter_by(id=post_id, user_id=user.id).delete()
    #    log_operation(db, post_id, "delete", user.id)
    db.delete(post)
    db.commit()

def log_operation(session, post_id: int, operation: str, user_id: int):
    new_history = History(post_id=post_id, operation=operation, user_id=user_id)
    session.add(new_history)
    session.commit()

def get_history(db):
    history = db.query(History).order_by(History.timestamp.desc()).all()
    result = []
    for h in history:
        timestamp_utc = h.timestamp
        timestamp_moscow = timestamp_utc + timedelta(hours=3)
        if h.post:
            post_title = h.post.title
        else:
            post_title = "Название удалённого поста скрыто"
        result.append({
            "post_title": post_title,
            "operation": h.operation,
            "username": h.user.username,
            "timestamp": timestamp_moscow.strftime("%H:%M:%S %d/%m/%Y")
        })
    return result

def clear_history():
    session = SessionLocal()
    session.query(History).delete()
    session.commit()
    session.close()
