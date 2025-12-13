import httpx
from functools import lru_cache
from app import config
from typing import Optional,Dict,Literal
import logging

logger=logging.getLogger(__name__)

@lru_cache
def get_settings():
    return config.Settings()

settings=get_settings()

class GoogleOAuth:
    def __init__(self):
        self.client_id=settings.GOOGLE_CLIENT_ID
        self.client_secret=settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri_web=settings.GOOGLE_REDIRECT_URI_WEB
        self.redirect_uri_mobile=settings.GOOGLE_REDIRECT_URI_MOBILE
        self.authorize_url="https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url="https://oauth2.googleapis.com/token"
        self.user_info_url="https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self,state:Optional[str]=None,platform:Literal["web","mobile"]="web")->str:
        redirect_uri=self.redirect_uri_web if platform == "web" else self.redirect_uri_mobile
        params = {"client_id": self.client_id,"redirect_uri": redirect_uri,"response_type": "code",
                  "scope": "openid email profile","access_type": "offline","prompt": "consent"}
        if state:
            params["state"] = state
        query_string="&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"
    async def exchange_code_for_token(self,code:str,platform:Literal["web","mobile"]="web")->Optional[str]:
        redirect_uri = self.redirect_uri_web if platform == "web" else self.redirect_uri_mobile
        try:
            async with httpx.AsyncClient() as client:
                response=await client.post(
                    self.token_url,
                    data={"client_id": self.client_id,"client_secret": self.client_secret,
                          "code": code,"redirect_uri": redirect_uri,"grant_type": "authorization_code"},
                          headers={"Accept": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    access_token = data.get("access_token")
                    if access_token:
                        logger.info("Successfully obtained Google access token")
                        return access_token
                    else:
                        logger.error(f"No access token in response: {data}")
                        return None
                else:
                    logger.error(f"Failed to get access token: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                headers={"Authorization": f"Bearer {access_token}","Accept": "application/json"}
                user_response=await client.get(self.user_info_url, headers=headers)
                if user_response.status_code != 200:
                    logger.error(f"Failed to get user info: {user_response.status_code}")
                    return None
                user_data = user_response.json()
                logger.info(f"Successfully retrieved Google user info for: {user_data.get('email')}")
                return {"id": user_data.get("id"),"email": user_data.get("email"),"name": user_data.get("name"),
                        "verified_email": user_data.get("verified_email", False)}
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None

google_oauth = GoogleOAuth()