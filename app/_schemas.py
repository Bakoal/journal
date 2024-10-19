from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class RecordCreate(BaseModel):
    data: str

class RecordUpdate(BaseModel):
    data: str

'''
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Схема для создания записи (Record)
class RecordCreate(BaseModel):
    content: str

# Схема для отображения записи (Record) с деталями
class Record(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: int

    class Config:
        orm_mode = True

# Схема для создания пользователя (UserCreate)
class UserCreate(BaseModel):
    email: str
    username: str
    password: str

# Схема для отображения пользователя (User) с деталями
class User(BaseModel):
    id: int
    email: str
    username: str

    class Config:
        orm_mode = True
'''