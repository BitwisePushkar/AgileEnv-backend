import httpx
from functools import lru_cache
from app import config
from typing import Optional, Dict, Literal
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

@lru_cache
def get_settings():
    return config.Settings()

settings = get_settings()

class GoogleOAuth:
    def __init__(self):
        self.client_id_web = settings.GOOGLE_CLIENT_ID
        self.client_secret_web = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri_web = settings.GOOGLE_REDIRECT_URI_WEB
        self.redirect_uri_mobile = settings.GOOGLE_REDIRECT_URI_MOBILE
        self.authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"

    def get_authorization_url(self,state: Optional[str] = None,platform: Literal["web", "mobile"] = "web") -> str:
        client_id = self.client_id_web
        redirect_uri = (self.redirect_uri_web if platform == "web"else self.redirect_uri_mobile)
        params = {"client_id": client_id,"redirect_uri": redirect_uri,"response_type": "code",
                  "scope": "openid email profile","access_type": "offline","prompt": "consent",}
        if state:
            params["state"] = state
        return f"{self.authorize_url}?{urlencode(params)}"
    async def exchange_code_for_token(self,code: str,platform: Literal["web", "mobile"] = "web") -> Optional[str]:
        client_id = self.client_id_web
        client_secret = self.client_secret_web
        redirect_uri = (self.redirect_uri_web if platform == "web"else self.redirect_uri_mobile)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.token_url,data={"client_id": client_id,"client_secret": client_secret,"code": code,
                                                                  "redirect_uri": redirect_uri,"grant_type": "authorization_code",},headers={"Accept": "application/json"},)
            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.status_code} - {response.text}")
                return None
            data = response.json()
            access_token = data.get("access_token")
            if not access_token:
                logger.error(f"No access token in response: {data}")
                return None
            logger.info(f"Google access token obtained (platform={platform})")
            return access_token
        except Exception as e:
            logger.exception("Error exchanging Google auth code")
            return None
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.user_info_url,headers={"Authorization": f"Bearer {access_token}","Accept": "application/json",},)
            if response.status_code != 200:
                logger.error(f"Failed to get Google user info: {response.status_code}")
                return None
            user_data = response.json()
            return {"id": user_data.get("id"),"email": user_data.get("email"),"name": user_data.get("name"),
                    "picture": user_data.get("picture"),"verified_email": user_data.get("verified_email", False),}
        except Exception as e:
            logger.exception("Error fetching Google user info")
            return None

google_oauth = GoogleOAuth()