from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.auth import schemas 
from app.auth import crud
from app.utils.dbUtil import get_db
from app.utils.passUtil import hash_pwd,verify_pass
from app.utils import JWTUtil
from datetime import timedelta
# from app.celery_app import celery_app
from app.tasks.email_tasks import send_otp_email


router = APIRouter()

@router.post("/api/register", status_code=status.HTTP_201_CREATED)
def register(user:schemas.UserCreate,db:Session=Depends(get_db)):
    exist_user = crud.user_exist(db, user.email)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
    pwd_hash = hash_pwd(user.password)
    db_user = crud.save_user(user,db,pwd_hash)
    access_token=JWTUtil.create_token(data={"sub":db_user.email,"user_id":db_user.id})
    refresh_token=JWTUtil.refresh_token(data={"sub":db_user.email,"user_id":db_user.id})
    return {"access_token":access_token,"refresh_token": refresh_token,"token_type":"Bearer",
            "user": {"id": db_user.id,"email": db_user.email,"username": db_user.username}}

@router.post("/api/login",status_code=status.HTTP_200_OK,response_model=schemas.Token)
def login(form_data:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    db_user=crud.get_user_and_username(db,form_data.username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid username/Email or Password",
                            headers={"WWW-Authenticate":"Bearer"})
    if not verify_pass(form_data.password,db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid username/Email or Password",
                            headers={"WWW-Authenticate":"Bearer"})
    if db_user.status!='1':
        db_user.status='1'
        db.commit()
        db.refresh(db_user)
        
    access_token=JWTUtil.create_token(data={"sub":db_user.email,"user_id":db_user.id})
    refresh_token=JWTUtil.refresh_token(data={"sub":db_user.email,"user_id":db_user.id})
    return {"access_token":access_token,"refresh_token": refresh_token,"token_type":"Bearer"}

@router.post("/api/refresh",response_model=schemas.Token)
def refresh_token(refresh:schemas.RefreshToken,db:Session=Depends(get_db)):
    payload=JWTUtil.decode_token(refresh.refresh_token)
    if payload is None or payload.get("type")!="refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid refresh token",
                            headers={"WWW-Authenticate":"Bearer"})
    email=payload.get("sub")
    user_id=payload.get("user_id")
    db_user=crud.get_user_email(db,email)
    if not db_user or db_user.status!='1':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user not found or inactive")
    access_token=JWTUtil.create_token(data={"sub":email,"user_id":user_id})
    return {"access_token":access_token,"token_type":"Bearer"}

@router.post("/api/logout")
def logout(token:str=Depends(JWTUtil.oauth_schema),current_user:str=Depends(JWTUtil.get_user),
           db:Session=Depends(get_db)):
    crud.add_token_blacklist(db,token)
    return{"message":"Successfull logout"}

@router.put("/api/resetpassword")
def resetpassword(password_new:schemas.PasswordReset,current_user=Depends(JWTUtil.get_user)
                  ,db:Session=Depends(get_db)):
    new_pass=hash_pwd(password_new.password)
    user=crud.update_password_id(db,current_user.id,new_pass)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,details="failed to update password")
    return {"message": "Password changed successfully"}

@router.delete("/api/deactivate")
def deactivate(token:str=Depends(JWTUtil.oauth_schema),current_user=Depends(JWTUtil.get_user),
                  db:Session=Depends(get_db)):
    deactivate=crud.deactivate_user(db,current_user.email)
    if not deactivate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to deactivate account")
    crud.add_token_blacklist(db,token)
    return{"message":"successfully deactivated","email":current_user.email}

@router.delete("/api/delete")
def delete(token:str=Depends(JWTUtil.oauth_schema),current_user=Depends(JWTUtil.get_user),
                  db:Session=Depends(get_db)):
    crud.add_token_blacklist(db,token)
    deleted=crud.delete_user(db,current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to delete account")
    return{"message":"successfully deleted account","email":current_user.email}

@router.post("/api/send-otp")
def send_otp(request: schemas.OTPRequest, db: Session = Depends(get_db)):

    if request.purpose == "registration":
        existing_user = crud.user_exist(db, request.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    if request.purpose == "password_reset":
        user = crud.get_user_email(db, request.email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    otp_code = crud.create_otp(db, request.email, request.purpose)
    send_otp_email.delay(request.email, otp_code, request.purpose)
    
    return {
        "message": "OTP sent successfully",
        "email": request.email
    }
@router.post("/api/verify-otp")
def verify_otp(request: schemas.OTPVerify, db: Session = Depends(get_db)):
    is_valid = crud.verify_otp(db, request.email, request.otp_code, request.purpose)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    crud.mark_otp_as_used(db, request.email, request.otp_code, request.purpose)
    
    return {"message": "OTP verified successfully"}


@router.post("/api/resend-otp")
def resend_otp(request: schemas.OTPRequest, db: Session = Depends(get_db)):
    otp_code = crud.create_otp(db, request.email, request.purpose)
    send_otp_email.delay(request.email, otp_code, request.purpose)
    
    return {
        "message": "OTP resent successfully",
        "email": request.email
    }

@router.post("/api/forgot-password")
def forgot_password(request: schemas.EmailRequest, db: Session = Depends(get_db)):
    user = crud.get_user_email(db, request.email)
    if not user:
        return {"message": "If email exists, OTP has been sent"}  
    otp_code = crud.create_otp(db, request.email, "password_reset")
    send_otp_email.delay(request.email, otp_code, "password_reset")
    
    return {"message": "If email exists, OTP has been sent"}

@router.post("/api/reset-password-with-otp")
def reset_password_with_otp(
    email: str,
    otp_code: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    is_valid = crud.verify_otp(db, email, otp_code, "password_reset")
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
    crud.mark_otp_as_used(db, email, otp_code, "password_reset")
    new_pass_hash = hash_pwd(new_password)
    user = crud.update_password(db, email, new_pass_hash)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update password"
        )
    
    return {"message": "Password reset successfully"}