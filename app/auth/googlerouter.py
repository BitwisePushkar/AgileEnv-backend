from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from app.auth import schemas, crud
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.utils.googleUtil import google_oauth
import logging
import secrets

router = APIRouter()
logger = logging.getLogger(__name__)
csrf_states = {}

@router.get("/api/auth/google/login")
async def google_login(request: Request):
    state = secrets.token_urlsafe(32)
    csrf_states[state] = True
    auth_url = google_oauth.get_authorized_url(state=state)
    
    logger.info("Generated Google authorization URL")
    
    return {
        "authorization_url": auth_url,
        "message": "Redirect user to this URL"
    }


@router.post("/api/auth/google/callback", response_model=schemas.GoogleAuthResponse)
async def google_callback(
    request: Request,
    callback: schemas.GoogleCallBack,
    db: Session = Depends(get_db)
):
    if callback.state not in csrf_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    del csrf_states[callback.state]

    access_token = await google_oauth.exchange_code_for_token(callback.code)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code for access token"
        )

    google_user = await google_oauth.get_user_info(access_token)
    
    if not google_user or not google_user.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to get user information from Google"
        )
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
            username = google_user.get("given_name", google_user["email"].split("@")[0])
            counter = 1
            original_username = username
            while crud.get_user_and_username(db, username):
                username = f"{original_username}{counter}"
                counter += 1
            user = crud.create_oauth_user(
                db=db,
                email=google_user["email"],
                username=username,
                provider="google",
                provider_user_id=provider_user_id
            )
            logger.info(f"Created new user via Google OAuth: {user.email}")
    jwt_access_token = JWTUtil.create_token(
        data={"sub": user.email, "user_id": user.id}
    )
    jwt_refresh_token = JWTUtil.refresh_token(
        data={"sub": user.email, "user_id": user.id}
    )
    return {
        "access_token": jwt_access_token,
        "refresh_token": jwt_refresh_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "google_profile": {
                "name": google_user.get("name"),
                "picture": google_user.get("picture"),
                "given_name": google_user.get("given_name"),
                "family_name": google_user.get("family_name"),
                "locale": google_user.get("locale")
            }
        }
    }


@router.post("/api/auth/google/link")
async def link_google_account(
    request: Request,
    link_request: schemas.OAuthLink,
    current_user=Depends(JWTUtil.get_user),
    db: Session = Depends(get_db)
):
    access_token = await google_oauth.exchange_code_for_token(link_request.code)
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code"
        )
    
    # Get Google user info
    google_user = await google_oauth.get_user_info(access_token)
    
    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve Google user information"
        )
    
    provider_user_id = str(google_user["id"])
    existing_oauth = crud.get_user_oauth(db, "google", provider_user_id)
    
    if existing_oauth and existing_oauth.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This Google account is already linked to another user"
        )
    crud.link_oauth_account(db, current_user.id, "google", provider_user_id)
    
    logger.info(f"User {current_user.email} linked Google account")
    
    return {
        "message": "Google account successfully linked",
        "google_email": google_user.get("email"),
        "google_name": google_user.get("name")
    }


@router.delete("/api/auth/google/unlink")
async def unlink_google_account(
    request: Request,
    current_user=Depends(JWTUtil.get_user),
    db: Session = Depends(get_db)
):
    if not current_user.password:
        oauth_accounts = crud.get_user_oauth_account(db, current_user.id)
        
        if len(oauth_accounts) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot unlink Google account. Set a password first or link another account."
            )
    success = crud.unlink_oauth_account(db, current_user.id, "google")
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google account not linked"
        )
    
    logger.info(f"User {current_user.email} unlinked Google account")
    
    return {"message": "Google account successfully unlinked"}