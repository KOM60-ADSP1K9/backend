"""
Main entry
"""

from fastapi import FastAPI

from src.core.error_handler import add_global_exception_handlers
from src.features.homepage.homepage_controller import homepage_router
from src.features.auth.auth_controller import auth_router
from src.features.found_report.found_report_controller import found_report_router
from src.features.lost_report.lost_report_controller import lost_report_router
from src.features.lokasi.lokasi_controller import lokasi_router
from src.features.kategori_barang.kategori_barang_controller import (
    kategori_barang_router,
)
from src.features.user.user_controller import user_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_global_exception_handlers(app)

# Auth module (public + protected)
app.include_router(auth_router)

# Lost report module (protected)
app.include_router(lost_report_router)

# Found report module (authenticated users)
app.include_router(found_report_router)

# Homepage module (protected – authenticated)
app.include_router(homepage_router)

# User module (protected – Staff only)
app.include_router(user_router)

# Lokasi module (protected – authenticated)
app.include_router(lokasi_router)

# Kategori barang module (protected – authenticated)
app.include_router(kategori_barang_router)
