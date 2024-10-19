from sqlalchemy.orm import Session
from .models import User, Record, OperationHistory
from .schemas import UserCreate, RecordCreate, RecordUpdate
from fastapi import HTTPException, status

# Работа с пользователями
def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, password=user.password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Работа с записями
def create_record(db: Session, record: RecordCreate, user: User):
    new_record = Record(data=record.data, created_by=user)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    # Логирование операции
    history_entry = OperationHistory(operation="create", user=user)
    db.add(history_entry)
    db.commit()

    return new_record

def update_record(db: Session, record_id: int, record_data: RecordUpdate, user: User):
    db_record = db.query(Record).filter(Record.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Только автор или администратор могут редактировать запись
    if db_record.created_by_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    db_record.data = record_data.data
    db.commit()

    # Логирование операции
    history_entry = OperationHistory(operation="update", user=user)
    db.add(history_entry)
    db.commit()

    return db_record

def delete_record(db: Session, record_id: int, user: User):
    db_record = db.query(Record).filter(Record.id == record_id).first()
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    # Только автор или администратор могут удалять запись
    if db_record.created_by_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(db_record)
    db.commit()

    # Логирование операции
    history_entry = OperationHistory(operation="delete", user=user)
    db.add(history_entry)
    db.commit()

    return {"detail": "Record deleted"}

def get_operation_history(db: Session):
    return db.query(OperationHistory).all()
