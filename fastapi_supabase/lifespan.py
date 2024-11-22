from typing import Awaitable, Callable, Optional, TypedDict
from fastapi import HTTPException
from supabase import AsyncClient, create_async_client
from supabase.lib.client_options import AsyncClientOptions
from gotrue.types import User

import logging

logger = logging.getLogger(__name__)
UserLoaderType = Callable[[AsyncClient, str], Awaitable[Optional[User]]]

class SupabaseLifespan(TypedDict):
    supabase: AsyncClient
    supabase_user_loader: UserLoaderType

async def user_loader_func(client: AsyncClient, access_token: Optional[str]):
    if not access_token:
        raise HTTPException(401, "Unauthorized")

    user_resp = await client.auth.get_user(access_token)
    if user_resp:
        return user_resp.user

async def lifespan(
    supabase_url: str,
    supabase_key: str,
    *,
    options: Optional[AsyncClientOptions] = None,
    user_loader: UserLoaderType = user_loader_func
) -> SupabaseLifespan:
    client = await create_async_client(
        supabase_url=supabase_url, supabase_key=supabase_key, options=options
    )
    return {"supabase": client, "supabase_user_loader": user_loader}
