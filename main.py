from location_generator import *
from load_data import load_data
from model import *
from notification import *
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import shutil
from typing import Dict
import secrets
from pathlib import Path

app = FastAPI(debug=True)
templates = Jinja2Templates(directory="static")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/img", StaticFiles(directory="static/img"), name="img")
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/lib", StaticFiles(directory="static/lib"), name="lib")
app.mount("/js", StaticFiles(directory="static/js"), name="js")
app.mount("/temp", StaticFiles(directory="static/temp"), name="temp")
app.mount("/out", StaticFiles(directory="static/out"), name="out")

# Simple in-memory storage for users
users_db: Dict[str, dict] = {}
sessions: Dict[str, str] = {}

# Helper functions
def create_session(username: str) -> str:
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = username
    return session_id

def get_current_user(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    return sessions.get(session_id) if session_id else None

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = users_db.get(username)
    
    if not user or user["password"] != password:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="session_id", value=create_session(username), httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, message: str = "", error: str = ""):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": message,
        "error": error
    })

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords don't match"
        })
    
    if username in users_db:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Username already exists"
        })
    
    users_db[username] = {"password": password}
    
    response = templates.TemplateResponse("register.html", {
        "request": request,
        "message": "Account created successfully! Redirecting to login..."
    })
    response.headers["Refresh"] = "2; url=/login"
    return response

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/login")
    response.delete_cookie("session_id")
    return response

# Page routes
@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login")
    return FileResponse("static/index.html")

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login")
    return FileResponse("static/about.html")

@app.get("/project", response_class=HTMLResponse)
async def project_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login")
    return FileResponse("static/project.html")

# Smart route handler for all other requests
@app.get("/{path:path}")
async def serve_static_or_template(request: Request, path: str):
    # Handle static files
    static_file = Path("static") / path
    if static_file.exists():
        return FileResponse(str(static_file))
    
    # Handle HTML templates
    if path.endswith('.html') or '.' not in path:
        title = path.split('.')[0] if '.' in path else path
        template_path = f"{title}.html"
        full_path = Path("static") / template_path
        
        if not get_current_user(request):
            return RedirectResponse(url="/login")
        
        if full_path.exists():
            return templates.TemplateResponse(template_path, {"request": request, "title": title})
    
    raise HTTPException(status_code=404)

# Video processing route
given_lat = 22.606803
given_lon = 85.338173
max_distance_km = 20

@app.post("/upload/")
async def predict_video(
    video: UploadFile = File(...), 
    selected_class: str = Form(...), 
    getAlert: bool = Form(False)
):
    temp_video_path = f"temp/{video.filename}"
    os.makedirs("static/temp", exist_ok=True)
    with open(f'static/{temp_video_path}', "wb") as f:
        shutil.copyfileobj(video.file, f)

    result, predicted_video_path = predictVideo(temp_video_path, selected_class)
    updated_result = add_random_location(result, given_lat, given_lon, max_distance_km)
    
    if getAlert:
        sendAlert(updated_result)

    return JSONResponse(content={
        "video_data_uri": temp_video_path,
        "predicted_video_url": predicted_video_path,
        "results": updated_result
    })