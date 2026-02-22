from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi import Form
class UserUpdateIn(BaseModel):
    """
    Admin panel orqali user ma'lumotlarini qisman yangilash uchun sxema.
    Barcha maydonlar ixtiyoriy, faqat yuborilganlari o'zgaradi.
    """
    username: Optional[str]
    passport: Optional[str]
    email: Optional[EmailStr]
    full_name: Optional[str]
    turniked_id: Optional[str]

    @classmethod
    def as_form(
            cls,
            username: Optional[str] = Form(None),
            passport: Optional[str] = Form(None),
            email: Optional[EmailStr] = Form(None),
            full_name: Optional[str] = Form(None),
            turniked_id: Optional[str] = Form(None),
    ) -> "UserUpdateIn":
        return cls(username=username, passport=passport, email=email, full_name=full_name, turniked_id=turniked_id)
