from fastapi import APIRouter, Request, Form, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from services.schemas import UserCreate, UserLogin
from services.crud import create_new_post, update_blog_post, delete_blog_post, clear_history, get_current_user, create_user, verify_user, set_cookie


post_router = APIRouter()

templates = Jinja2Templates(directory="templates")

@post_router.post("/auth/register")
async def register(email: str = Form(...), username: str = Form(...), password: str = Form(...)):
    user = UserCreate(email=email, username=username, password=password)
    create_user(user.email, user.username, user.password)
    return RedirectResponse("/auth/login", status_code=303)

@post_router.post("/auth/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    user = UserLogin(username=username, password=password)
    user_id = verify_user(user.username, user.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    set_cookie(response, "user_id", str(user_id))
    return RedirectResponse("/", status_code=303)

@post_router.post("/create_post")
async def create_post(request: Request, title: str = Form(...), content: str = Form(...)):
    username = get_current_user(request)
    create_new_post(title, content, username)
    return RedirectResponse("/", status_code=303)

@post_router.post("/edit_post/{post_id}")
async def edit_post(request: Request, post_id: int, title: str = Form(...), content: str = Form(...)):
    username = get_current_user(request)
    update_blog_post(post_id, title, content, username)
    return RedirectResponse("/", status_code=303)

@post_router.post("/delete_post/{post_id}")
async def delete_post(request: Request, post_id: int):
    username = get_current_user(request)
    delete_blog_post(post_id, username)
    return RedirectResponse("/", status_code=303)

@post_router.post("/history/clear")
async def clear_history_route(request: Request):
    clear_history()
    return RedirectResponse("/history", status_code=303)