# fastapi-supabase

Integrate supabase to FastAPI with less effort

## Installation

```sh
pip install fastapi-supabase
```

For local development:

```sh
uv sync
uv pip install -e .
```

## Usage

This module needs to initialize the Supabase client object during the lifespan event. You can do it like this:

```py
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield await fastapi_supabase.lifespan(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(
    title="FastAPI Supabase",
    lifespan=lifespan # Here we add a function to handle when the app starts up.
)
# You're all set!
```

We provide some dependency functions, which help you access supabase client on FastAPI endpoints.

### `SupabaseClient`

This type helps you access supabase asynchronous clients.

Example usage:

```python
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
```

### `SupabaseSession`

This type is same as `SupabaseClient`. The difference is this type adds access token to supabase client automatically and endpoint will be protected.

### `CurrentUser`

This type is to get the current user object. And, if you use this type, your endpoint will not be accessible if the client request does not provide a Bearer access token. The access token must be valid on the supabase.

Example:

```python
@app.get("/book")
async def list_book(sp: SupabaseSession, current_user: CurrentUser, page: int = 1, limit: int = 10):
    """
    List of books with pagination.
    """
    tbl = sp.table("books")
    offset = (page - 1) * limit
    resp = await tbl.select("*").eq("user_id", current_user.id).limit(limit).offset(offset).execute()
    return resp.data
```
