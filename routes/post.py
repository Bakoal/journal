from fastapi import APIRouter, Request, Form, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from services.schemas import UserCreate, UserLogin
from services.crud import get_posts, create_new_post, update_blog_post, delete_blog_post, clear_history, get_current_user, create_user, verify_user, get_db
from sqlalchemy.orm import Session


post_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@post_router.post("/auth/register")
def register_user(user_data: UserCreate = Form(...), db: Session = Depends(get_db)):
    new_user = create_user(user_data, db)
    return RedirectResponse("/auth/login", status_code=303)

@post_router.post("/auth/login")
def login_user(request: Request, user_data: UserLogin = Form(...), db: Session = Depends(get_db)):
    user, error_message = verify_user(user_data, db)
    if error_message:
        return templates.TemplateResponse("login.html", {"request": request, "error_message": error_message})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(key="username", value=user.username, httponly=True)
    return response

@post_router.post("/create_post")
async def create_post(request: Request, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    username = get_current_user(request)
    create_new_post(title, content, username, db)
    return RedirectResponse("/", status_code=303)

@post_router.post("/edit_post/{post_id}")
async def update_post(request: Request, post_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    username = get_current_user(request)
    update_blog_post(post_id, title, content, username, db)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)

@post_router.post("/edit_post/{post_id}")
async def edit_post(request: Request, post_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db)):
    username = get_current_user(request)
    update_blog_post(post_id, title, content, username)
    return RedirectResponse("/", status_code=303)

@post_router.post("/delete_post/{post_id}")
async def delete_post(request: Request, post_id: int, db: Session = Depends(get_db)):
    username = get_current_user(request)
    posts = get_posts(db)
    try:
        delete_blog_post(post_id, username, db)
        return RedirectResponse("/", status_code=303)
    except HTTPException as e:
        return templates.TemplateResponse("index.html", {"request": request, "username": username, "posts": posts, "error": e.detail})

@post_router.post("/history/clear")
async def clear_history_route():
    clear_history()
    return RedirectResponse("/history", status_code=303)