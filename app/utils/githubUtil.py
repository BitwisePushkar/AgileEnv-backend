import httpx
from functools import lru_cache
from app import config
from typing import Optional,Dict
import logging

logger=logging.getLogger(__name__)

@lru_cache
def get_settings():
    return config.Settings()

settings=get_settings()

class GitHubOAuth:
    def __init__(self):
        self.client_id=settings.GITHUB_CLIENT_ID
        self.client_secret=settings.GITHUB_CLIENT_SECRET
        self.redirect_uri=settings.GITHUB_REDIRECT_URI
        self.authorize_url="https://github.com/login/oauth/authorize"
        self.token_url="https://github.com/login/oauth/access_token"
        self.user_api_url="https://api.github.com/user"
        self.user_emails_url="https://api.github.com/user/emails"

    def get_authorized_url(self,state:Optional[str]=None)->str:
        params={"client_id":self.client_id,"redirect_uri":self.redirect_uri,"scope":"user:email"}
        if state:
            params["state"]=state
        query_string="&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"
    
    async def exchange_code_for_token(self,code:str)->Optional[str]:
        try:
            async with httpx.AsyncClient() as client:
                response=await client.post(self.token_url,data={"client_id": self.client_id,"client_secret":self.client_secret,
                                                                "code":code,"redirect_uri":self.redirect_uri,},headers={"Accept":"application/json"})
                if response.status_code==200:
                    data=response.json()
                    access_token=data.get("access_token")
                    if access_token:
                        logger.info("Successfully got access token")
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
    
    async def get_user_info(self,access_token:str)->Optional[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                headers={"Authorization": f"Bearer {access_token}","Accept": "application/json"}
                user_response=await client.get(self.user_api_url, headers=headers)
                if user_response.status_code!=200:
                    logger.error(f"Failed to get user info: {user_response.status_code}")
                    return None
                user_data = user_response.json()
                if not user_data.get("email"):
                    emails_response=await client.get(self.user_emails_url, headers=headers)
                    if emails_response.status_code==200:
                        emails=emails_response.json()
                        for email_obj in emails:
                            if email_obj.get("primary") and email_obj.get("verified"):
                                user_data["email"] = email_obj["email"]
                                break
                logger.info(f"Successfully retrieved user info for GitHub ID: {user_data.get('id')}")
                return {"id": user_data.get("id"),"login": user_data.get("login"),"email": user_data.get("email"),
                        "name": user_data.get("name"),"avatar_url": user_data.get("avatar_url"),"bio": user_data.get("bio"),"location": user_data.get("location"),}  
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
    
github_oauth = GitHubOAuth()