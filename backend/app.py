from datetime import datetime, timezone
from typing import Optional
from typing_extensions import Annotated
from uuid import UUID
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

import fastapi_supabase
import os

import dotenv
import logging

from fastapi_supabase.dependencies import CurrentUser, SupabaseClient, SupabaseSession

logging.basicConfig(level=logging.DEBUG)
for k, v in logging.Logger.manager.loggerDict.items():
    if not k.startswith(("fastapi_supabase", "uvicorn")):
        v.disabled = True

dotenv.load_dotenv(".env")

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield await fastapi_supabase.lifespan(SUPABASE_URL, SUPABASE_KEY)


app = FastAPI(title="FastAPI Supabase", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class BookIn(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

@app.post("/login")
async def login(sp: SupabaseClient, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Login and get access token
    """
    # login using email
    data = {
        "email": form_data.username,
        "password": form_data.password
    }
    resp = await sp.auth.sign_in_with_password(data)
    if resp.user:
        access_token = None
        if resp.session:
            access_token = resp.session.access_token
        
        return {"access_token": access_token}
    raise HTTPException(400, "Invalid username or password")

@app.get("/book")
async def list_book(sp: SupabaseSession, current_user: CurrentUser, page: int = 1, limit: int = 10):
    """
    List of books with pagination.
    """
    tbl = sp.table("books")
    offset = (page - 1) * limit
    resp = await tbl.select("*").eq("user_id", current_user.id).limit(limit).offset(offset).execute()
    return resp.data


@app.post("/book")
async def create_book(book: BookIn, sp: SupabaseSession, current_user: CurrentUser):
    """
    Create a new book
    """
    # check if book already exist
    tbl = sp.table("books")
    resp = await tbl.select("name").eq("name", book.name).limit(1).execute()
    if resp and resp.data:
        raise HTTPException(400, "Book already exists")
    
    data = book.model_dump()
    data["user_id"] = current_user.id
    resp = await tbl.insert(book.model_dump()).execute()
    if resp and resp.data:
        return resp.data[0]

    raise HTTPException(400, "Something went wrong")


@app.put("/book/{book_id}")
async def update_book(book_id: UUID, book: BookIn, sp: SupabaseSession, current_user: CurrentUser):
    """
    Update book
    """
    tbl = sp.table("books")
    resp = await tbl.select("name").eq("name", book.name).limit(1).execute()
    if resp and resp.data:
        raise HTTPException(400, "Book already exists")

    data = book.model_dump()
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = await tbl.update(data).match({"id": str(book_id), "user_id": current_user.id}).execute()
    if resp and resp.data:
        return {}
    raise HTTPException(404, "Book not found")

@app.delete("/book/{book_id}")
async def delete_book(book_id: UUID, sp: SupabaseSession, current_user: CurrentUser):
    """
    Delete book
    """
    tbl = sp.table("books")
    resp = await tbl.delete().eq("id", str(book_id)).eq("user_id", current_user.id).execute()
    if resp and resp.data:
        return {}
    raise HTTPException(404, "Book not found")
