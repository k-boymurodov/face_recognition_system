from typing import Literal

from pydantic import BaseModel, Field, field_validator


Role = Literal["admin", "operator", "reports"]
EmployeeStatus = Literal["active", "inactive"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=72)
    role: Role

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Login bo'sh bo'lishi mumkin emas")
        return value

    @field_validator("password")
    @classmethod
    def password_max_bytes(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Parol 72 baytdan oshmasin.")
        return value


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=1, max_length=50)
    position: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=32)
    status: EmployeeStatus = "active"

    @field_validator("employee_code", "name", "department", "position")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Maydon bo'sh bo'lishi mumkin emas")
        return value


class EmployeeUpdate(BaseModel):
    employee_code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=1, max_length=50)
    position: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=32)
    status: EmployeeStatus | None = None


class UserView(BaseModel):
    id: int
    username: str
    role: Role
