from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from services.crud import get_post, get_posts, get_current_user, get_history


get_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@get_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    username = get_current_user(request)
    posts = get_posts()
    return templates.TemplateResponse("index.html", {"request": request, "username": username, "posts": posts})

@get_router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@get_router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@get_router.get("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("user_id")
    return RedirectResponse("/auth/login", status_code=303)

@get_router.get("/post/{post_id}", response_class=HTMLResponse)
async def read_post(request: Request, post_id: int):
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    username = get_current_user(request)
    return templates.TemplateResponse("post.html", {"request": request, "post": post, "username": username})

@get_router.get("/create_post", response_class=HTMLResponse)
async def create_post_form(request: Request):
    username = get_current_user(request)
    return templates.TemplateResponse("create_post.html", {"request": request, "username": username})

@get_router.get("/edit_post/{post_id}", response_class=HTMLResponse)
async def edit_post_form(request: Request, post_id: int):
    username = get_current_user(request)
    post = get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse("edit_post.html", {"request": request, "username": username, "post": post})

@get_router.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    history = get_history()
    return templates.TemplateResponse("history.html", {"request": request, "history": history})