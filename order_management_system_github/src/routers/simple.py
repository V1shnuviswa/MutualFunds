from fastapi import APIRouter, Depends, Body
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..dependencies import db_dependency, current_user_dependency

router = APIRouter(
    prefix="/simple",
    tags=["simple"],
)

@router.post("/test")
async def test_endpoint(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(db_dependency),
    current_user = Depends(current_user_dependency)
):
    """Simple test endpoint"""
    return {
        "message": "Test successful",
        "user": current_user.username,
        "payload": payload
    } 