from fastapi import APIRouter, HTTPException, status, Depends,Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth import schemas 
from app.auth import crud
from app.utils.dbUtil import get_db
from app.utils.passUtil import hash_pwd,verify_pass
from app.utils import JWTUtil
from app.utils.emailUtil import send_otp_email
import logging 
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import timedelta

limiter=Limiter(key_func=get_remote_address)

router = APIRouter()
logger=logging.getLogger(__name__)

@router.post("/api/register/", status_code=status.HTTP_201_CREATED,response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def register(request:Request,user:schemas.UserCreate,db:Session=Depends(get_db)):
    exist_user = crud.user_exist(db, user.email)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
    exist_username=crud.get_user_and_username(db,user.username)
    if exist_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="username already taken")
    pwd_hash = hash_pwd(user.password)
    try:
        db_user = crud.save_user_unverified(user,db,pwd_hash)
    except IntegrityError as e:
        db.rollback()
        error_msg = str(e.orig).lower()
        if 'email' in error_msg or 'Email' in str(e.orig):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered")
        elif 'username' in error_msg or 'UserName' in str(e.orig):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already taken.")
        else:
            logger.error(f"Database integrity error during registration: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Registration failed. Please try again.")
    is_locked,minutes_remaining=crud.is_otp_locked(db,user.email,"registration")
    if is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Too many failed OTP attempts.Try again in {minutes_remaining} minutes.")
    otp=crud.create_otp(db,user.email,"registration")
    if otp is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="unable to send otp")
    send_otp_email(user.email,otp,"registration",user.username)
    logger.info(f"Registration OTP sent to: {user.email}")
    return {"message":"sent email successfully","email":user.email}

@router.post("/api/verify-registration/",response_model=schemas.OTPResponse)
@limiter.limit("10/minute")
def verify_registration(request:Request,otp:schemas.OTPVerify,db:Session=Depends(get_db)):
    is_valid,attempts_remaining,error_message=crud.verify_and_delete_otp(db,otp.email,otp.otp_code,otp.purpose)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid or expired otp")
    user=crud.verify_email(db,otp.email)
    logger.info(f"email sucessfully verified")
    return {"message":"email verified successfully","email":user.email}

@router.post("/api/resend-otp/",response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def resend_otp(request:Request,req:schemas.OTPRequest,db:Session=Depends(get_db)):
    user=crud.get_user_email(db,req.email)
    if req.purpose=="registration":
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="email already verified")
        is_locked,minutes_remaining=crud.is_otp_locked(db,user.email,"registration")
        if is_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Too many failed OTP attempts.Try again in {minutes_remaining} minutes.")
        otp=crud.create_otp(db,user.email,"registration")
        if otp is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="unable to send otp")
        send_otp_email(user.email,otp,"registration",user.username)
        logger.info(f"Registration OTP resent to: {user.email}")
        return {"message":"email resent successfully","email":user.email}
    elif req.purpose=="password_reset":
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
        if user.password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="user loged in through oauth so can't change password")
        is_locked,minutes_remaining=crud.is_otp_locked(db,req.email,"password_reset")
        if is_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Too many failed OTP attempts.Try again in {minutes_remaining} minutes.")
        otp=crud.create_otp(db,req.email,"password_reset")
        if otp is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="unable to send otp")
        send_otp_email(req.email,otp,"password_reset")
        logger.info(f"Registration OTP resent to: {req.email}")
        return {"message":"email resent successfully","email":req.email}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid purpose")

@router.post("/api/login/",status_code=status.HTTP_200_OK,response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request:Request,data:schemas.UserLogin,db:Session=Depends(get_db)):
    db_user=crud.get_user_and_username(db,data.username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid username/Email or Password")
    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="email not verified")
    if not verify_pass(data.password,db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid username/Email or Password")
    if not db_user.is_active:
        crud.reactivate_user(db,db_user.email)
        logger.info(f"Account reactivated on login: {db_user.email}")
    access_token=JWTUtil.create_token(data={"sub":db_user.email,"user_id":db_user.id})
    refresh_token=JWTUtil.refresh_token(data={"sub":db_user.email,"user_id":db_user.id})
    logger.info(f"User logged in successfully: {db_user.email}")
    return {"access_token":access_token,"refresh_token": refresh_token,"token_type":"Bearer"}

@router.post("/api/refresh/",response_model=schemas.Token)
@limiter.limit("20/minute")
def refresh_token(request:Request,refresh:schemas.RefreshToken,db:Session=Depends(get_db)):
    payload=JWTUtil.decode_token(refresh.refresh_token)
    if payload is None or payload.get("type")!="refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid refresh token",
                            headers={"WWW-Authenticate":"Bearer"})
    email=payload.get("sub")
    user_id=payload.get("user_id")
    db_user=crud.get_user_email(db,email)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user not found or inactive")
    access_token=JWTUtil.create_token(data={"sub":email,"user_id":user_id})
    new_refresh=JWTUtil.refresh_token(data={"sub":email,"user_id":user_id})
    return {"access_token":access_token,"refresh_token":new_refresh,"token_type":"Bearer"}

@router.post("/api/logout/")
@limiter.limit("30/minute")
def logout(request: Request,token:str=Depends(JWTUtil.oauth_schema),current_user:str=Depends(JWTUtil.get_user),
           db:Session=Depends(get_db)):
    crud.add_token_blacklist(db,token)
    logger.info(f"User logged out: {current_user.email}")
    return{"message":"Successfull logout"}

@router.put("/api/deactivate/")
@limiter.limit("5/minute")
def deactivate(request: Request,token:str=Depends(JWTUtil.oauth_schema),current_user=Depends(JWTUtil.get_user),
                  db:Session=Depends(get_db)):
    deactivate=crud.deactivate_user(db,current_user.email)
    if not deactivate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to deactivate account")
    crud.add_token_blacklist(db,token)
    logger.info(f"Account deactivated: {current_user.email}")
    return{"message":"successfully deactivated","email":current_user.email}

@router.delete("/api/delete/")
@limiter.limit("3/minute")
def delete(request: Request,token:str=Depends(JWTUtil.oauth_schema),current_user=Depends(JWTUtil.get_user),
                  db:Session=Depends(get_db)):
    crud.add_token_blacklist(db,token)
    deleted=crud.delete_user(db,current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="failed to delete account")
    logger.info(f"Account permanently deleted: {current_user.email}")
    return{"message":"successfully deleted account","email":current_user.email}

@router.post("/api/forget-password/",response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def forget_password(request: Request,req:schemas.EmailRequest,db:Session=Depends(get_db)):
    user=crud.user_exist(db,req.email)
    if not user or user.password is None:
        return schemas.OTPResponse(message="if email exists, otp sent",email=req.email)
    is_locked,minutes_remaining=crud.is_otp_locked(db, req.email, "password_reset")
    if is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"Too many failed OTP attempts.Try again in {minutes_remaining} minutes.")
    otp=crud.create_otp(db,req.email,"password_reset")
    if otp is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="unable to send otp")
    send_otp_email(req.email,otp,"password_reset")
    logger.info(f"Password reset OTP sent to: {req.email}")
    return {"message":"email sent successfully","email":req.email}

@router.post("/api/verify-reset-otp/",response_model=schemas.PasswordResetToken)
@limiter.limit("10/minute")
def verify_reset_otp(request: Request,data:schemas.PasswordResetRequest,db:Session=Depends(get_db)):
    is_valid,attempts_remaining,error_message=crud.verify_and_delete_otp(db, data.email, data.otp, "password_reset")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid or expired otp")
    reset_token=JWTUtil.create_token(data={"sub":data.email,"type":"password_reset","purpose":"reset_password"},
                                     expire_delta=timedelta(minutes=5))
    logger.info(f"Password reset token generated for: {data.email}")
    return{"message":"otp verified","reset_token":reset_token,"expires_in":300}

@router.put("/api/complete-reset/")
@limiter.limit("5/minute")
def complete_reset(request:Request,data:schemas.PasswordResetComplete,db:Session=Depends(get_db)):
    payload=JWTUtil.decode_token(data.reset_token)
    if not payload:
        logger.warning(f"Invalid or Expired token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired token")
    if payload.get("type")!="password_reset":
        logger.warning(f"Wrong tokn type")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="wrong token type")
    email=payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="invalid payload")
    new_pass=hash_pwd(data.password)
    user=crud.update_password(db,email,new_pass)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    crud.add_token_blacklist(db,data.reset_token)
    logger.info(f"Password reset successfully for: {email}")
    return {"message": "Password reset successfully","email":email}