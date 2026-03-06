from fastapi import APIRouter, HTTPException, status, Depends, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth import schemas, crud
from app.auth.models import User
from app.utils.dbUtil import get_db
from app.utils.passUtil import hash_pwd, verify_pass
from app.utils import JWTUtil
from app.utils.email.email_tasks import send_otp_task
from app.utils.S3Util import s3_upload, s3_delete, validate_image
from app.utils.redisUtils import redis_client
from app.auth.schemas import SUPPORTED_LANGUAGE_TAGS
from typing import Optional
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import timedelta
from app.utils.settings import settings

router = APIRouter()
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

_ACCESS_TOKEN_TTL = settings.JWT_ACCESS_TOKEN_EXPIRE_DAYS * 86400
_REFRESH_TOKEN_TTL = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400

@router.post("/api/register/", status_code=status.HTTP_201_CREATED, response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    lang = "en"
    exist_user = crud.get_user_email(db, user.email)
    if exist_user:
        if exist_user.is_verified:
            if exist_user.password is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="This email is already registered via Google/GitHub login.",)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Email already registered.",)
        else:
            logger.info("Re-registration attempt for unverified email")
            if exist_user.username != user.username:
                username_taken = crud.get_user_and_username(db, user.username)
                if username_taken and username_taken.id != exist_user.id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Username already taken.",)
            pwd_hash = hash_pwd(user.password)
            try:
                crud.update_user_unverified(db=db, email=user.email, username=user.username, pwd=pwd_hash)
                logger.info("Updated unverified user")
            except IntegrityError as e:
                db.rollback()
                if "username" in str(e.orig).lower():
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
                logger.error(f"Unexpected IntegrityError during update: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Update failed.")
    else:
        exist_username = crud.get_user_and_username(db, user.username)
        if exist_username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
        pwd_hash = hash_pwd(user.password)
        try:
            crud.save_user_unverified(user, db, pwd_hash)
            logger.info("New user registered (unverified)")
        except IntegrityError as e:
            db.rollback()
            error_msg = str(e.orig).lower()
            if "email" in error_msg:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")
            elif "username" in error_msg:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken.")
            logger.error("Database integrity error during registration")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed.")
    otp = crud.create_otp(db, user.email, "registration")
    if otp is None:
        send_locked, send_min = crud.is_otp_send_locked(db, user.email, "registration")
        if send_locked:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"Too many OTP requests. Try again in {send_min} minutes.",)
        verify_locked, verify_min = crud.is_otp_locked(db, user.email, "registration")
        if verify_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"OTP verification locked. Try again in {verify_min} minutes.",)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to send OTP.")
    send_otp_task.delay(user.email, otp, "registration", user.username, language=lang)
    logger.info("OTP sent for registration")
    return {"message": "Verification email sent successfully.", "email": user.email}

@router.post("/api/verify-registration/", response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def verify_registration(request: Request, otp: schemas.OTPVerify, db: Session = Depends(get_db)):
    is_valid, attempts_remaining, error_message = crud.verify_and_delete_otp(db, otp.email, otp.otp_code, "registration")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message or "Invalid or expired OTP")
    user = crud.verify_email(db, otp.email)
    logger.info("Email successfully verified")
    return {"message": "Email verified successfully.", "email": user.email}

@router.post("/api/resend-otp/", response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def resend_otp(request: Request, req: schemas.OTPRequest, db: Session = Depends(get_db)):
    lang = "en"
    user = crud.get_user_email(db, req.email)
    if req.purpose == "registration":
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.is_verified:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified.")
    elif req.purpose == "password_reset":
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        if user.password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Account uses OAuth login — cannot reset password.",)
        profile = crud.get_profile_id(db, user.id)
        lang = profile.language if profile and profile.language else "en"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid purpose.")
    otp = crud.create_otp(db, req.email, req.purpose)
    if otp is None:
        send_locked, send_min = crud.is_otp_send_locked(db, req.email, req.purpose)
        if send_locked:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"Too many OTP requests. Try again in {send_min} minutes.",)
        verify_locked, verify_min = crud.is_otp_locked(db, req.email, req.purpose)
        if verify_locked:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=f"OTP verification locked. Try again in {verify_min} minutes.",)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to send OTP.")
    send_otp_task.delay(req.email,otp,req.purpose,user.username if req.purpose == "registration" else "User",language=lang,)
    logger.info(f"OTP resent for purpose={req.purpose}")
    return {"message": "OTP resent successfully.", "email": req.email}

@router.post("/api/login/", status_code=status.HTTP_200_OK, response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request: Request, data: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_and_username(db, data.username)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not db_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    if db_user.password is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use Google/GitHub to login.")
    if not verify_pass(data.password, db_user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not db_user.is_active:
        crud.reactivate_user(db, db_user.email)
        logger.info("Account reactivated on login")
    access_token = JWTUtil.create_token(data={"sub": db_user.email, "user_id": db_user.id})
    new_refresh_token = JWTUtil.refresh_token(data={"sub": db_user.email, "user_id": db_user.id})
    logger.info("User logged in successfully")
    return {"access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "Bearer",
            "username": db_user.username,
            "email": db_user.email,
            }

@router.post("/api/refresh/", response_model=schemas.Token)
@limiter.limit("20/minute")
def refresh_token_endpoint(request: Request, refresh: schemas.RefreshToken, db: Session = Depends(get_db)):
    if redis_client.is_token_blacklisted(refresh.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Refresh token has been revoked. Please log in again.",)
    if crud.token_blacklisted(db, refresh.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Refresh token has been revoked. Please log in again.",)
    payload = JWTUtil.decode_token(refresh.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid refresh token",
                            headers={"WWW-Authenticate": "Bearer"},)
    email = payload.get("sub")
    user_id = payload.get("user_id")
    db_user = crud.get_user_email(db, email)
    if not db_user or not db_user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    new_access = JWTUtil.create_token(data={"sub": email, "user_id": user_id})
    new_refresh = JWTUtil.refresh_token(data={"sub": email, "user_id": user_id})
    return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "Bearer"}

@router.post("/api/logout/")
@limiter.limit("30/minute")
def logout(request: Request,body: Optional[schemas.LogoutRequest] = None,auth: JWTUtil.AuthContext = Depends(JWTUtil.get_auth_context),
           db: Session = Depends(get_db),):
    redis_client.blacklist_token(auth.token, _ACCESS_TOKEN_TTL)
    crud.add_token_blacklist(db, auth.token)
    if body and body.refresh_token:
        refresh_payload = JWTUtil.decode_token(body.refresh_token)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            redis_client.blacklist_token(body.refresh_token, _REFRESH_TOKEN_TTL)
            crud.add_token_blacklist(db, body.refresh_token)
    logger.info("User logged out")
    return {"message": "Logged out successfully"}

@router.put("/api/deactivate/")
@limiter.limit("5/minute")
def deactivate(request: Request,body: Optional[schemas.LogoutRequest] = None,auth: JWTUtil.AuthContext = Depends(JWTUtil.get_auth_context),
               db: Session = Depends(get_db),):
    deactivated = crud.deactivate_user(db, auth.user.email)
    if not deactivated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to deactivate account")
    redis_client.blacklist_token(auth.token, _ACCESS_TOKEN_TTL)
    crud.add_token_blacklist(db, auth.token)
    if body and body.refresh_token:
        refresh_payload = JWTUtil.decode_token(body.refresh_token)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            redis_client.blacklist_token(body.refresh_token, _REFRESH_TOKEN_TTL)
            crud.add_token_blacklist(db, body.refresh_token)
    logger.info("Account deactivated")
    return {"message": "Account deactivated successfully", "email": auth.user.email}

@router.delete("/api/delete/")
@limiter.limit("3/minute")
def delete(request: Request,body: Optional[schemas.LogoutRequest] = None,auth: JWTUtil.AuthContext = Depends(JWTUtil.get_auth_context),
           db: Session = Depends(get_db),):
    redis_client.blacklist_token(auth.token, _ACCESS_TOKEN_TTL)
    crud.add_token_blacklist(db, auth.token)
    if body and body.refresh_token:
        refresh_payload = JWTUtil.decode_token(body.refresh_token)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            redis_client.blacklist_token(body.refresh_token, _REFRESH_TOKEN_TTL)
            crud.add_token_blacklist(db, body.refresh_token)
    deleted = crud.delete_user(db, auth.user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete account")
    logger.info("Account permanently deleted")
    return {"message": "Account deleted successfully", "email": auth.user.email}

@router.post("/api/forget-password/", response_model=schemas.OTPResponse)
@limiter.limit("5/minute")
def forget_password(request: Request, req: schemas.EmailRequest, db: Session = Depends(get_db)):
    user = crud.user_exist(db, req.email)
    if not user or user.password is None:
        return schemas.OTPResponse(message="If the email exists, an OTP has been sent.", email=req.email)
    profile = crud.get_profile_id(db, user.id)
    lang = profile.language if profile and profile.language else "en"
    otp = crud.create_otp(db, req.email, "password_reset")
    if otp is None:
        send_locked, send_min = crud.is_otp_send_locked(db, req.email, "password_reset")
        if send_locked:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,detail=f"Too many OTP requests. Try again in {send_min} minutes.",)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unable to send OTP.")
    send_otp_task.delay(req.email, otp, "password_reset", language=lang)
    logger.info("Password reset OTP sent")
    return {"message": "If the email exists, an OTP has been sent.", "email": req.email}

@router.post("/api/verify-reset-otp/", response_model=schemas.PasswordResetToken)
@limiter.limit("10/minute")
def verify_reset_otp(request: Request, data: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    is_valid, attempts_remaining, error_message = crud.verify_and_delete_otp(db, data.email, data.otp, "password_reset")
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message or "Invalid or expired OTP")
    reset_token = JWTUtil.create_token(data={"sub": data.email, "type": "password_reset", "purpose": "reset_password"},
                                       expire_delta=timedelta(minutes=5),)
    logger.info("Password reset token generated")
    return {"message": "OTP verified", "reset_token": reset_token, "expires_in": 300}

@router.put("/api/complete-reset/")
@limiter.limit("5/minute")
def complete_reset(request: Request, data: schemas.PasswordResetComplete, db: Session = Depends(get_db)):
    payload = JWTUtil.decode_token(data.reset_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    if payload.get("type") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wrong token type")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    new_pass = hash_pwd(data.password)
    user = crud.update_password(db, email, new_pass)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud.add_token_blacklist(db, data.reset_token)
    logger.info("Password reset successfully")
    return {"message": "Password reset successfully", "email": email}

@router.post("/api/app/pre/", response_model=schemas.EmailCheckResponse)
@limiter.limit("20/minute")
def check_email_exists(request: Request, req: schemas.EmailRequest, db: Session = Depends(get_db)):
    user = crud.get_user_email(db, req.email)
    if user:
        return {"is_email": True, "is_verified": user.is_verified}
    return {"is_email": False, "is_verified": None}

@router.post("/api/set-password/")
@limiter.limit("5/minute")
def set_password(request: Request,data: schemas.SetPassword,current_user: User = Depends(JWTUtil.get_user),
                 db: Session = Depends(get_db),):
    if current_user.password is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Password already set. Use change-password instead.",)
    pwd_hash = hash_pwd(data.password)
    updated_user = crud.update_password_id(db, current_user.id, pwd_hash)
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info("Password set for OAuth user")
    return {"message": "Password set successfully.", "email": current_user.email}

@router.get("/api/profile/", response_model=schemas.ProfileResponse)
@limiter.limit("30/minute")
def get_profile(request: Request,current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    profile = crud.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info("Profile fetched")
    return profile

@router.post("/api/profile/", response_model=schemas.ProfileResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def create_profile(request: Request,name: Optional[str] = Form(None),post: Optional[str] = Form(None),
                   reason: Optional[str] = Form(None),language: Optional[str] = Form(None),image: Optional[UploadFile] = File(None),
                   current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    exist = crud.get_profile_id(db, current_user.id)
    if exist:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profile already exists.")
    profile_data = {}
    if name is not None:
        name = name.strip()
        if len(name) < 2 or len(name) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be 2–100 characters.")
        profile_data["name"] = name
    if post is not None:
        post = post.strip()
        if len(post) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post must not exceed 100 characters.")
        profile_data["post"] = post
    if reason is not None:
        reason = reason.strip()
        if len(reason) > 1000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reason must not exceed 1000 characters.")
        profile_data["reason"] = reason
    if language is not None:
        language = language.strip().lower()
        if language not in SUPPORTED_LANGUAGE_TAGS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language tag.")
        profile_data["language"] = language
    image_url = None
    if image:
        file_content = image.file.read()
        if not validate_image(image.filename, len(file_content)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is too large.")
        image_url = s3_upload(file_content, image.filename, image.content_type)
        if not image_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image.")
        profile_data["image_url"] = image_url
    try:
        crud.create_profile(db, current_user.id, profile_data)
        logger.info("Profile created")
        return crud.get_profile(db, current_user.id)
    except Exception as e:
        if image_url:
            s3_delete(image_url)
        logger.error(f"Profile creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create profile.")

@router.put("/api/profile/", response_model=schemas.ProfileResponse)
@limiter.limit("10/minute")
def update_profile(request: Request,name: Optional[str] = Form(None),post: Optional[str] = Form(None),
                   reason: Optional[str] = Form(None),language: Optional[str] = Form(None),image: Optional[UploadFile] = File(None),
                   current_user: User = Depends(JWTUtil.get_user),db: Session = Depends(get_db),):
    exist = crud.get_profile_id(db, current_user.id)
    if not exist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    profile_data = {}
    if name is not None:
        name = name.strip()
        if len(name) < 2 or len(name) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be 2–100 characters.")
        profile_data["name"] = name
    if post is not None:
        post = post.strip()
        if len(post) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Post must not exceed 100 characters.")
        profile_data["post"] = post
    if reason is not None:
        reason = reason.strip()
        if len(reason) > 1000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reason must not exceed 1000 characters.")
        profile_data["reason"] = reason
    if language is not None:
        language = language.strip().lower()
        from app.auth.schemas import SUPPORTED_LANGUAGE_TAGS
        if language not in SUPPORTED_LANGUAGE_TAGS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported language tag.")
        profile_data["language"] = language
    old_image_url = None
    new_image_url = None
    if image:
        file_content = image.file.read()
        if not validate_image(image.filename, len(file_content)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is too large.")
        new_image_url = s3_upload(file_content, image.filename, image.content_type)
        if not new_image_url:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload image.")
        old_image_url = exist.image_url
        profile_data["image_url"] = new_image_url

    try:
        crud.update_profile(db, current_user.id, profile_data)
        logger.info("Profile updated")
        if old_image_url and new_image_url:
            if not s3_delete(old_image_url):
                logger.warning("Failed to delete old profile image from S3")
        return crud.get_profile(db, current_user.id)
    except Exception as e:
        if new_image_url:
            s3_delete(new_image_url)
        logger.error(f"Profile update failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile.")