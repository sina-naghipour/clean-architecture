# auth/models.py
from .connection import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from sqlalchemy import Enum
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class UserModel(Base):
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="userrole", values_callable=lambda enum: [e.value for e in enum],),
        nullable=False,default=UserRole.USER,)   
    referred_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    referral_code = Column(String(50), unique=True, nullable=True)
    referral_created_at = Column(DateTime(timezone=True), nullable=True)
    
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())