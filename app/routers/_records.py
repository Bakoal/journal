from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal
from app.schemas import RecordCreate, Record
from app.crud import create_record, get_records, get_record_by_id, update_record, delete_record, log_operation
from app.models import User

router = APIRouter()

# Получить все записи
@router.get("/records/", response_model=List[Record])
async def get_all_records(db: Session = Depends(SessionLocal)):
    records = await get_records(db)
    return records

# Получить запись по ID
@router.get("/records/{record_id}", response_model=Record)
async def get_single_record(record_id: int, db: Session = Depends(SessionLocal)):
    record = await get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

# Добавить новую запись
@router.post("/records/", response_model=Record)
async def add_record(record: RecordCreate, db: Session = Depends(SessionLocal), current_user: User = Depends()):
    new_record = await create_record(db, record, user_id=current_user.id)
    await log_operation(db, new_record.id, current_user.id, action="add")
    return new_record

# Обновить существующую запись
@router.put("/records/{record_id}", response_model=Record)
async def edit_record(record_id: int, record: RecordCreate, db: Session = Depends(SessionLocal), current_user: User = Depends()):
    existing_record = await get_record_by_id(db, record_id)
    if not existing_record:
        raise HTTPException(status_code=404, detail="Record not found")
    updated_record = await update_record(db, existing_record, record)
    await log_operation(db, record_id, current_user.id, action="edit")
    return updated_record

# Удалить запись
@router.delete("/records/{record_id}")
async def remove_record(record_id: int, db: Session = Depends(SessionLocal), current_user: User = Depends()):
    record = await get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    await delete_record(db, record)
    await log_operation(db, record_id, current_user.id, action="delete")
    return {"detail": "Record deleted successfully"}

'''
from app.schemas import RecordCreate  # Убедитесь, что этот импорт правильный
from app.crud import create_record, log_operation
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal

router = APIRouter()

@router.post("/records/")
async def add_record(record: RecordCreate, db: Session = Depends(SessionLocal)):
    new_record = await create_record(db, record)
    await log_operation(db, new_record.id, user_id=1, action="add")
    return new_record

# Подобные маршруты для редактирования, удаления и истории
'''