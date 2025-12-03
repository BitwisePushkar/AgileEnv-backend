from pydantic import BaseModel,Field,EmailStr,ConfigDict

class UserCreate(BaseModel):
    email: EmailStr

#made this to hide data not return   
class UserResponse(BaseModel):
    id:int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)