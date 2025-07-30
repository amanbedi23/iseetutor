"""Onboarding API routes for new user setup."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ...database.base import get_db
from ...database.models import User
from ...core.security.auth import get_current_user
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class OnboardingProfile(BaseModel):
    """Profile data from onboarding wizard."""
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=5, le=18)
    grade: int = Field(..., ge=1, le=12)
    avatar: dict = Field(..., description="Avatar selection with id, emoji, color")
    voice_speed: float = Field(default=1.0, ge=0.5, le=1.5)
    onboarding_complete: bool = True


class OnboardingStatus(BaseModel):
    """Check if user needs onboarding."""
    needs_onboarding: bool
    profile_complete: bool
    has_voice_calibration: bool


@router.get("/status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OnboardingStatus:
    """Check if current user needs onboarding."""
    metadata = current_user.metadata or {}
    
    return OnboardingStatus(
        needs_onboarding=not metadata.get("onboarding_complete", False),
        profile_complete=bool(current_user.age and current_user.grade),
        has_voice_calibration=metadata.get("voice_calibrated", False)
    )


@router.post("/complete")
async def complete_onboarding(
    profile: OnboardingProfile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete onboarding and save user profile."""
    try:
        # Update user profile
        current_user.full_name = profile.name
        current_user.age = profile.age
        current_user.grade = profile.grade
        
        # Update metadata
        if not current_user.metadata:
            current_user.metadata = {}
            
        current_user.metadata.update({
            "avatar": profile.avatar,
            "voice_speed": profile.voice_speed,
            "onboarding_complete": True,
            "onboarding_date": datetime.utcnow().isoformat(),
            "voice_calibrated": True  # Set after voice test
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "user_id": current_user.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skip")
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Skip onboarding (for returning users or testing)."""
    if not current_user.metadata:
        current_user.metadata = {}
        
    current_user.metadata["onboarding_complete"] = True
    current_user.metadata["onboarding_skipped"] = True
    
    db.commit()
    
    return {"success": True, "message": "Onboarding skipped"}


class VoiceCalibration(BaseModel):
    """Voice calibration settings."""
    voice_speed: float = Field(..., ge=0.5, le=1.5)
    wake_word_sensitivity: float = Field(default=0.5, ge=0.1, le=1.0)


@router.put("/voice-calibration")
async def update_voice_calibration(
    calibration: VoiceCalibration,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update voice calibration settings."""
    if not current_user.metadata:
        current_user.metadata = {}
        
    current_user.metadata.update({
        "voice_speed": calibration.voice_speed,
        "wake_word_sensitivity": calibration.wake_word_sensitivity,
        "voice_calibrated": True,
        "voice_calibration_date": datetime.utcnow().isoformat()
    })
    
    db.commit()
    
    return {
        "success": True,
        "voice_speed": voice_speed,
        "wake_word_sensitivity": wake_word_sensitivity
    }