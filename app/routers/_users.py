from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import SessionLocal
from app.schemas import UserCreate, User
from app.crud import create_user, get_user_by_username
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Регистрация пользователя
@router.post("/users/", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(SessionLocal)):
    db_user = await get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    new_user = await create_user(db, user, hashed_password)
    return new_user

# Логин пользователя и получение токена
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(SessionLocal)):
    user = await get_user_by_username(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    # Генерация фиктивного токена (обычно это JWT или OAuth токен)
    return {"access_token": user.username, "token_type": "bearer"}

# Функция для получения текущего пользователя
@router.get("/users/me", response_model=User)
async def read_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
    user = await get_user_by_username(db, token)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
    return user
