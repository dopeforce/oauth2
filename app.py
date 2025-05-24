import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth

# Load .env
load_dotenv()

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="a-very-secret-key")

# Set up OAuth
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/")
async def homepage(request: Request):
    user = request.session.get("user")
    if user:
        return f"Hello {user['email']}"
    
    if "code" in request.query_params:
        token = await oauth.google.authorize_access_token(request)
        request.session["user"] = token["userinfo"]
        request.session["id_token"] = token["id_token"]
        return RedirectResponse("/")
    
    return await oauth.google.authorize_redirect(request, request.url)

@app.get("/id_token")
async def get_id_token(request: Request):
    id_token = request.session.get("id_token")
    if not id_token:
        return JSONResponse({"error": "User not authenticated"}, status_code=401)
    return JSONResponse({
        "id_token": id_token,
        "client_id": os.getenv("GOOGLE_CLIENT_ID")
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
