from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.crud import get_post, get_posts, get_current_user, get_history, get_db
from sqlalchemy.orm import Session


get_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@get_router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    username = get_current_user(request)
    posts = get_posts(db)
    return templates.TemplateResponse("index.html", {"request": request, "username": username, "posts": posts})

@get_router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@get_router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@get_router.get("/auth/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie(key="username")
    return response

@get_router.get("/post/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    username = get_current_user(request)
    post = get_post(post_id, db)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("post.html", {"request": request, "username": username, "post": post})

@get_router.get("/create_post", response_class=HTMLResponse)
async def create_post_form(request: Request):
    username = get_current_user(request)
    return templates.TemplateResponse("create_post.html", {"request": request, "username": username})

@get_router.get("/edit_post/{post_id}", response_class=HTMLResponse)
async def edit_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    username = get_current_user(request)
    post = get_post(post_id, db)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("edit_post.html", {"request": request, "username": username, "post": post})

@get_router.get("/history", response_class=HTMLResponse)
async def history(request: Request, db: Session = Depends(get_db)):
    username = get_current_user(request)
    history = get_history(db)
    return templates.TemplateResponse("history.html", {"request": request, "username": username, "history": history})