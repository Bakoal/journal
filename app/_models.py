from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    data = Column(String)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_by = relationship("User")
    created_at = Column(DateTime, default=datetime.utcnow)

class OperationHistory(Base):
    __tablename__ = "operation_history"
    id = Column(Integer, primary_key=True, index=True)
    operation = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")
    timestamp = Column(DateTime, default=datetime.utcnow)
