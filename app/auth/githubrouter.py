from fastapi import APIRouter, HTTPException, status, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.auth import schemas, crud
from app.utils.dbUtil import get_db
from app.utils import JWTUtil
from app.utils.githubUtil import github_oauth
from typing import Literal
import logging
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/auth/github/login/")
@limiter.limit("10/minute")
async def github_login(request: Request,platform:Literal["web","mobile"]=Query(default="web"),db:Session=Depends(get_db)):
    crud.exp_state(db)
    state = secrets.token_urlsafe(32)
    crud.create_state(db=db,state=state,platform=platform,provider="github",exp_min=10)
    auth_url = github_oauth.get_authorized_url(state=state, platform=platform)
    logger.info(f"Generated GitHub authorization URL for {platform}")
    return {"authorization_url": auth_url,"message": "Redirect user to this URL","platform": platform}

@router.post("/api/auth/github/callback/")
@limiter.limit("10/minute")
async def github_callback(request:Request,callback:schemas.GitHubCallBack,platform:Literal["web","mobile"]=Query(default="mobile"),db:Session=Depends(get_db)):
    state_data = crud.get_delete_state(db=db,state=callback.state,provider="github")
    if not state_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Invalid or expired state parameter")
    access_token = await github_oauth.exchange_code_for_token(callback.code, platform=platform)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to exchange auth code")
    github_user = await github_oauth.get_user_info(access_token)
    if not github_user or not github_user.get("email"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to get user info")
    provider_user_id = str(github_user["id"])
    existing_user = crud.get_user_oauth(db, "github", provider_user_id)
    if existing_user:
        logger.info(f"GitHub user logged in: {existing_user.email}")
        user = existing_user
    else:
        user_by_email = crud.get_user_email(db, github_user["email"])
        if user_by_email:
            crud.link_oauth_account(db, user_by_email.id, "github", provider_user_id)
            logger.info(f"Linked GitHub account to existing user: {user_by_email.email}")
            user = user_by_email
        else:
            username = github_user["login"]
            counter = 1
            original_username = username
            while crud.get_user_and_username(db, username):
                username = f"{original_username}{counter}"
                counter += 1
            user = crud.create_oauth_user(db=db,email=github_user["email"],username=username,provider="github",provider_user_id=provider_user_id)
            logger.info(f"Created new user via GitHub OAuth")
    jwt_access_token = JWTUtil.create_token(data={"sub": user.email, "user_id": user.id})
    jwt_refresh_token = JWTUtil.refresh_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": jwt_access_token,"refresh_token": jwt_refresh_token,"token_type": "Bearer","platform": platform,
            "user": {"id": user.id,"email": user.email,"username": user.username,
                     "github_profile": {"login": github_user.get("login"),"name": github_user.get("name")}}}

@router.post("/api/auth/github/link/")
@limiter.limit("5/minute")
async def link_github_account(request: Request,link_request: schemas.OAuthLink,platform: Literal["web", "mobile"] = Query(default="web"),current_user=Depends(JWTUtil.get_user),db: Session = Depends(get_db)):
    access_token = await github_oauth.exchange_code_for_token(link_request.code, platform=platform)
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to exchange authorization code")
    github_user = await github_oauth.get_user_info(access_token)
    if not github_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Failed to retrieve GitHub user information")
    provider_user_id = str(github_user["id"])
    existing_oauth = crud.get_user_oauth(db, "github", provider_user_id)
    if existing_oauth and existing_oauth.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="GitHub account already linked to another user")
    crud.link_oauth_account(db, current_user.id, "github", provider_user_id)
    logger.info(f"User {current_user.email} linked GitHub account")
    return {"message": "GitHub account successfully linked","github_username": github_user.get("login")}

@router.delete("/api/auth/github/unlink/")
@limiter.limit("5/minute")
async def unlink_github_account(request: Request,current_user=Depends(JWTUtil.get_user),db: Session = Depends(get_db)):
    if not current_user.password:
        oauth_accounts = crud.get_user_oauth_account(db, current_user.id)
        if len(oauth_accounts) <= 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Cannot unlink the only authentication method")
    success = crud.unlink_oauth_account(db, current_user.id, "github")
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="GitHub account not linked")
    logger.info(f"User {current_user.email} unlinked GitHub account")
    return {"message": "GitHub account successfully unlinked"}

@router.get("/api/auth/oauth/accounts/")
@limiter.limit("30/minute")
async def get_linked_accounts(request: Request,current_user=Depends(JWTUtil.get_user),db: Session = Depends(get_db)):
    oauth_accounts = crud.get_user_oauth_account(db, current_user.id)
    return {"linked_accounts": [{"provider": account.provider,"linked_at": account.created_at.isoformat()}
                                for account in oauth_accounts],"has_password": current_user.password is not None}