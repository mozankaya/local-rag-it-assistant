from fastapi import APIRouter

from app.api.routes import admin_dashboard, admin_users, auth, chat, feedback, health, users


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin_dashboard.router)
api_router.include_router(admin_users.router)
api_router.include_router(chat.router)
api_router.include_router(feedback.router)