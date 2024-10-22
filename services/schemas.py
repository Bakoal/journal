from pydantic import BaseModel, EmailStr


# Модель для регистрации пользователя
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

# Модель для входа пользователя
class UserLogin(BaseModel):
    username: str
    password: str

# Модель для создания поста
class PostCreate(BaseModel):
    title: str
    content: str
