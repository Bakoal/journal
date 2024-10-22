from db.models import User, Post, History
from db.init import SessionLocal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from services.schemas import UserCreate, UserLogin
import hashlib
from datetime import datetime


# Функция для хэширования паролей
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def get_current_user(request):
    username = request.cookies.get("username")
    if not username:
        return None
    return username

# Функции для работы с базой данных

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def log_operation(db: Session, post_title: str, operation: str, user_id: int):
    new_history = History(post_title=post_title, operation=operation, user_id=user_id, timestamp=datetime.now())
    db.add(new_history)
    db.commit()

def get_history(db: Session):
    history = db.query(History).order_by(History.timestamp.desc()).all()
    result = []
    for h in history:
        result.append({
            "post_title": h.post_title,
            "operation": h.operation,
            "username": h.user.username,
            "timestamp": h.timestamp.strftime("%H:%M:%S %d/%m/%Y")
        })
    return result

def clear_history():
    session = SessionLocal()
    session.query(History).delete()
    session.commit()
    session.close()

def verify_user(user_data: UserLogin, db: Session):
    user = db.query(User).filter(User.username == user_data.username).first()
    if user is None:
        return None, "Неверное имя пользователя или пароль"
    hashed_password = hash_password(user_data.password)
    if user.password != hashed_password:
        return None, "Неверное имя пользователя или пароль" 
    return user, None

def create_user(user_data: UserCreate, db: Session):
    user_exists = db.query(User).filter((User.email == user_data.email) | (User.username == user_data.username)).first()
    if user_exists:
        return "Пользователь с такой электронной почтой или именем уже существует"
    hashed_password = hash_password(user_data.password)
    new_user = User(email=user_data.email, username=user_data.username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return None

def get_posts(db: Session):
    posts = db.query(Post).all()
    return [{"id": post.id, "title": post.title, "content": post.content, "username": post.user.username} for post in posts]

def get_post(post_id: int, db: Session):
    post = db.query(Post).filter_by(id=post_id).first()
    if post:
        return {"id": post.id, "title": post.title, "content": post.content, "username": post.user.username if post.user else "Неизвестно"}
    return None

def create_new_post(title: str, content: str, username: str, db: Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    new_post = Post(
        title=title,
        content=content,
        user_id=user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    log_operation(db, new_post.title, "create", user.id)
    return new_post

def update_blog_post(post_id: int, title: str, content: str, username: str, db: Session):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return "Пост не найден"
        # raise HTTPException(status_code=404, detail="Пост не найден")
    if post.user.username != username:
        return "У вас нет разрешения на изменение этого поста"
        # raise HTTPException(status_code=403, detail="У вас нет разрешения на изменение этого поста")
    post.title = title
    post.content = content
    db.commit()
    db.refresh(post)
    log_operation(db, post.title, "edit", post.user_id)
    return None

def delete_blog_post(post_id: int, username: str, db: Session):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if post.user.username != username:
        raise HTTPException(status_code=403, detail="У вас нет разрешения на удаление этого поста")
    db.delete(post)
    db.commit()
    log_operation(db, post.title, "delete", post.user_id)