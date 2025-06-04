# /home/ubuntu/order_management_system/src/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import schemas, models, security, crud
from ..database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Note: Using OAuth2PasswordRequestForm expects 'username' and 'password' fields in form data.
    # The API structure defined uses JSON with userId, memberId, password.
    # Adjusting here to use OAuth2 form for simplicity, or would need a custom dependency
    # to parse the JSON body as defined in schemas.UserLogin.
    # Let's assume username maps to userId for now.
    user = crud.get_user_by_userid(db, user_id=form_data.username)
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.user_id, "member_id": user.member_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example endpoint to create a user (for testing purposes)
# In a real application, user creation might be handled differently.
@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_userid(db, user_id=user.user_id)
    if db_user:
        raise HTTPException(status_code=400, detail="UserID already registered")
    return crud.create_user(db=db, user=user)

