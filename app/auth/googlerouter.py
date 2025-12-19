from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from app.auth import schemas, crud
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.utils.googleUtil import google_oauth
from app.utils.redisUtils import redis_client
import logging
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Literal

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
logger = logging.getLogger(__name__)
STATE_EXPIRY = 600

@router.get("/api/auth/google/login/")
@limiter.limit("10/minute")
async def google_login(request: Request,platform: Literal["web", "mobile"] = Query("web")):
    state = secrets.token_urlsafe(32)
    redis_key = f"oauth:google:state:{state}"
    redis_client.set_with_expiry(redis_key, platform, STATE_EXPIRY)
    auth_url = google_oauth.get_authorization_url(state=state, platform=platform)
    logger.info(f"Generated Google authorization URL for platform: {platform}")
    return {"authorization_url": auth_url, "message": "Redirect user to this URL"}

@router.post("/api/auth/google/callback/", response_model=schemas.GoogleAuthResponse)
@limiter.limit("10/minute")
async def google_callback(request: Request,callback: schemas.GoogleCallBack,platform: Literal["web", "mobile"] = Query("web"),db: Session = Depends(get_db)):
    redis_key = f"oauth:google:state:{callback.state}"
    stored_platform = redis_client.get(redis_key)
    if not stored_platform:
        logger.warning(f"Invalid or expired state parameter: {callback.state}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired state parameter")
    if stored_platform != platform:
        logger.warning(f"Platform mismatch: stored={stored_platform}, received={platform}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Platform mismatch - possible CSRF attack")
    redis_client.delete(redis_key) 
    access_token = await google_oauth.exchange_code_for_token(callback.code, platform=platform)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to exchange auth code for access token")
    google_user = await google_oauth.get_user_info(access_token)
    if not google_user or not google_user.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to retrieve Google user info")
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
            base = username
            while crud.get_user_and_username(db, username):
                username = f"{base}{counter}"
                counter += 1
            user = crud.create_oauth_user(db=db,email=google_user["email"],username=username,
                                        provider="google",provider_user_id=provider_user_id,)
            logger.info(f"Created new user via Google OAuth")
    
    jwt_access_token = JWTUtil.create_token(data={"sub": user.email, "user_id": user.id})
    jwt_refresh_token = JWTUtil.refresh_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": jwt_access_token,"refresh_token": jwt_refresh_token,"token_type": "Bearer","user": {
        "id": user.id,"email": user.email,"username": user.username,"google_profile": {
            "name": google_user.get("name"),"picture": google_user.get("picture"),"email": google_user.get("email"),},},}
    
@router.get("/oauth/google/mobile-bridge")
async def google_mobile_bridge(code: str, state: str):
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8" />
        <title>This might take some seconds...</title>
      </head>
      <body>
        <script>
          window.location.href =
            "com.agile.app://auth/google/callback" +
            "?code={code}&state={state}";
        </script>
      </body>
    </html>
    """)

@router.post("/api/auth/google/link/")
@limiter.limit("5/minute")
async def link_google_account(request: Request,link_request: schemas.OAuthLink,current_user=Depends(JWTUtil.get_user),db: Session = Depends(get_db),platform: Literal["web", "mobile"] = Query("web")):
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
async def unlink_google_account(request: Request,current_user=Depends(JWTUtil.get_user),db: Session = Depends(get_db)):
    if not current_user.password:
        oauth_accounts = crud.get_user_oauth_account(db, current_user.id)
        if len(oauth_accounts) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot unlink the only authentication method. Set a password first.")
    success = crud.unlink_oauth_account(db, current_user.id, "google")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Google account not linked to this user")
    logger.info(f"User {current_user.email} unlinked Google account")
    return {"message": "Google account successfully unlinked"}