"""
Main entry
"""

from fastapi import FastAPI

from src.core.error_handler import add_global_exception_handlers
from src.features.auth.auth_controller import auth_router
from src.features.user.user_controller import user_router

app = FastAPI()
add_global_exception_handlers(app)

# Auth module (public + protected)
app.include_router(auth_router)

# User module (protected – Staff only)
app.include_router(user_router)
