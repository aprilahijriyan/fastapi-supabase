from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing_extensions import Annotated
from supabase import AsyncClient
from gotrue import User
from fastapi import Depends, HTTPException, Request, status
import logging

from .lifespan import SupabaseLifespan

logger = logging.getLogger(__name__)
bearer_token = HTTPBearer(auto_error=False)


async def get_supabase_client(req: Request) -> AsyncClient:
    try:
        supabase = req.state._state["supabase"]
        return supabase
    except KeyError as e:
        raise RuntimeError(
            "Supabase client not found. Perhaps you forgot to set it?"
        ) from e


SupabaseClient = Annotated[AsyncClient, Depends(get_supabase_client)]


async def get_access_token(
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_token)],
) -> str:
    access_token = creds.credentials
    logger.debug(f"access_token={access_token}")
    return access_token


async def get_current_user(
    req: Request, access_token: str = Depends(get_access_token)
) -> User:
    state: SupabaseLifespan = req.state._state
    sp_client = state["supabase"]
    user_loader = state["supabase_user_loader"]
    user_obj = await user_loader(sp_client, access_token)
    if not user_obj:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "You don't have permission")
    return user_obj


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_supabase_session(
    client: SupabaseClient,
    access_token: Optional[str] = Depends(get_access_token)
):
    auth_headers = {"Authorization": client._create_auth_header(access_token)}
    client.options.headers.update(auth_headers)
    await client.realtime.set_auth(access_token)
    return client


SupabaseSession = Annotated[AsyncClient, Depends(get_supabase_session)]
