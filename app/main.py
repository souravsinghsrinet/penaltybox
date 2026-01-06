from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import datetime
import os

app = FastAPI(title="PenaltyBox API", version="1.0.0")

# Configure CORS with environment-based origins
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
# This allows accessing files like: http://localhost:8000/uploads/proofs/image.png
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Import and include routers
from app.api.v1 import auth, groups, penalties, proofs, rules, users

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(penalties.router, prefix="/penalties", tags=["Penalties"])
app.include_router(proofs.router, prefix="/proofs", tags=["Proofs"])
app.include_router(rules.router, prefix="/groups", tags=["Rules"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
async def root():
    return {"message": "Welcome to PenaltyBox API"}

@app.get("/ping", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint to verify the API is running
    Returns:
        dict: A simple response indicating the API is running
    """
    return {
        "status": "healthy",
        "message": "PenaltyBox API is running",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
