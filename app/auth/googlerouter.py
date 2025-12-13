from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.auth import schemas, crud
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.utils.googleUtil import google_oauth
from typing import Literal
import logging
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address
from urllib.parse import urlencode

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
logger = logging.getLogger(__name__)
csrf_states = {}

@router.get("/api/auth/google/login/")
@limiter.limit("10/minute")
async def google_login(request: Request,platform:Literal["web","mobile"]=Query(default="web",description="Platform type")):
    state=secrets.token_urlsafe(32)
    csrf_states[state] = {"platform": platform}
    auth_url = google_oauth.get_authorization_url(state=state,platform=platform)
    logger.info("Generated Google authorization URL")
    return {"authorization_url": auth_url,"message": "Redirect user to this URL","platform": platform}

@router.get("/api/auth/google/callback/")
@limiter.limit("10/minute")
async def google_callback_get(request: Request,code: str = Query(...),state: str = Query(...),db: Session = Depends(get_db)):
    if state not in csrf_states:
        logger.warning(f"Invalid Google OAuth state")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired state parameter")
    platform_info = csrf_states.pop(state)
    platform = platform_info.get("platform", "web")
    access_token = await google_oauth.exchange_code_for_token(code, platform=platform)
    if not access_token:
        if platform == "web":
            error_url = f"{JWTUtil.settings.FRONTEND_WEB_URL}/auth/error?message=token_exchange_failed"
            return RedirectResponse(url=error_url)
        else:
            error_url = f"{JWTUtil.settings.FRONTEND_MOBILE_SCHEME}auth/error?message=token_exchange_failed"
            return RedirectResponse(url=error_url)
    google_user = await google_oauth.get_user_info(access_token)
    if not google_user or not google_user.get("email"):
        if platform == "web":
            error_url = f"{JWTUtil.settings.FRONTEND_WEB_URL}/auth/error?message=user_info_failed"
            return RedirectResponse(url=error_url)
        else:
            error_url = f"{JWTUtil.settings.FRONTEND_MOBILE_SCHEME}auth/error?message=user_info_failed"
            return RedirectResponse(url=error_url)
    if not google_user.get("verified_email"):
        if platform == "web":
            error_url = f"{JWTUtil.settings.FRONTEND_WEB_URL}/auth/error?message=email_not_verified"
            return RedirectResponse(url=error_url)
        else:
            error_url = f"{JWTUtil.settings.FRONTEND_MOBILE_SCHEME}auth/error?message=email_not_verified"
            return RedirectResponse(url=error_url)
    provider_user_id = str(google_user["id"])
    existing_user = crud.get_user_oauth(db, "google", provider_user_id)
    if existing_user:
        logger.info(f"Google user logged in: {existing_user.email}")
        user = existing_user
    else:
        user_by_email = crud.get_user_email(db, google_user["email"])
        if user_by_email:
            crud.link_oauth_account(db, user_by_email.id, "google", provider_user_id)
            logger.info(f"Linked Google account to existing user: {user_by_email.email}")
            user = user_by_email
        else:
            username = google_user["email"].split("@")[0]
            counter = 1
            original_username = username
            while crud.get_user_and_username(db, username):
                username = f"{original_username}{counter}"
                counter += 1
            user = crud.create_oauth_user(db=db,email=google_user["email"],username=username,
                                          provider="google",provider_user_id=provider_user_id)
            logger.info(f"Created new user via Google OAuth: {user.email}")
    jwt_access_token = JWTUtil.create_token(data={"sub": user.email, "user_id": user.id})
    jwt_refresh_token = JWTUtil.refresh_token(data={"sub": user.email, "user_id": user.id})
    if platform == "web":
        params = urlencode({"access_token": jwt_access_token,"refresh_token": jwt_refresh_token,"platform": "web"})
        redirect_url = f"{JWTUtil.settings.FRONTEND_WEB_URL}/auth/callback?{params}"
    else:
        params = urlencode({"access_token": jwt_access_token,"refresh_token": jwt_refresh_token,"platform": "mobile"})
        redirect_url = f"{JWTUtil.settings.FRONTEND_MOBILE_SCHEME}auth/callback?{params}"
    logger.info(f"Redirecting {platform} user after Google OAuth")
    return RedirectResponse(url=redirect_url)

@router.post("/api/auth/google/callback/", response_model=schemas.GoogleAuthResponse)
@limiter.limit("10/minute")
async def google_callback_post(request: Request,callback: schemas.GoogleCallBack,platform: Literal["web", "mobile"] = Query(default="mobile"),db: Session = Depends(get_db)):
    try:
        platform_info = csrf_states.pop(callback.state)
    except KeyError:
        logger.warning(f"Invalid Google OAuth state")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired state parameter")
    access_token = await google_oauth.exchange_code_for_token(callback.code, platform=platform)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to get access token")
    google_user = await google_oauth.get_user_info(access_token)
    if not google_user or not google_user.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to retrieve user info")
    if not google_user.get("verified_email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Google email not verified")
    provider_user_id = str(google_user["id"])
    existing_user = crud.get_user_oauth(db, "google", provider_user_id)
    if existing_user:
        logger.info(f"Google user logged in: {existing_user.email}")
        user = existing_user
    else:
        user_by_email = crud.get_user_email(db, google_user["email"])
        if user_by_email:
            crud.link_oauth_account(db, user_by_email.id, "google", provider_user_id)
            logger.info(f"Linked Google account to existing user: {user_by_email.email}")
            user = user_by_email
        else:
            username = google_user["email"].split("@")[0]
            counter = 1
            original_username = username
            while crud.get_user_and_username(db, username):
                username = f"{original_username}{counter}"
                counter += 1
            user = crud.create_oauth_user(db=db,email=google_user["email"],username=username,provider="google",
                                          provider_user_id=provider_user_id)
            logger.info(f"Created new user via Google OAuth: {user.email}")
    jwt_access_token = JWTUtil.create_token(data={"sub": user.email, "user_id": user.id})
    jwt_refresh_token = JWTUtil.refresh_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": jwt_access_token,"refresh_token": jwt_refresh_token,"token_type": "Bearer","platform": platform,
            "user": {"id": user.id,"email": user.email,"username": user.username,
                     "google_profile": {"name": google_user.get("name"),"picture": google_user.get("picture"),"email": google_user.get("email")}}}

@router.post("/api/auth/google/link/")
@limiter.limit("5/minute")
async def link_google_account(request: Request,link_request: schemas.OAuthLink,platform:Literal["web","mobile"]=Query(default="web"),current_user=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    access_token = await google_oauth.exchange_code_for_token(link_request.code, platform=platform)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to exchange auth code")
    google_user = await google_oauth.get_user_info(access_token)
    if not google_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to get user info")
    provider_user_id = str(google_user["id"])
    exist_oauth = crud.get_user_oauth(db, "google", provider_user_id)
    if exist_oauth and exist_oauth.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Google account already linked to another user")
    crud.link_oauth_account(db, current_user.id, "google", provider_user_id)
    logger.info(f"User {current_user.email} linked Google account")
    return {"message": "Google account successfully linked","google_email": google_user.get("email")}

@router.delete("/api/auth/google/unlink/")
@limiter.limit("5/minute")
async def unlink_google_account(request: Request,current_user=Depends(JWTUtil.get_user),db:Session=Depends(get_db)):
    if not current_user.password:
        oauth_accounts=crud.get_user_oauth_account(db, current_user.id)
        if len(oauth_accounts) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot unlink the only auth method.")
    success = crud.unlink_oauth_account(db, current_user.id, "google")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Google account not linked to this user")
    logger.info(f"User {current_user.email} unlinked Google account")
    return {"message": "Google account successfully unlinked"}