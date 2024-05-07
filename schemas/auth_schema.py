from pydantic import BaseModel


class CreateUser(BaseModel):
    name: str
    email: str
    password: str
    profile_pic: str
    coverage_pic: str
    status: str

class UserLogin(BaseModel):
    email: str
    password: str
