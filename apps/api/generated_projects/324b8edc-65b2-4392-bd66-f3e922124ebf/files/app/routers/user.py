from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "preferences": current_user.preferences
    }

@router.put("/me/preferences")
async def update_preferences(preferences: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.preferences = preferences
    db.commit()
    db.refresh(current_user)
    return {"message": "Preferences updated successfully"}
