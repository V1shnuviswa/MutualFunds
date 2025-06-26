from fastapi import APIRouter, Depends, HTTPException, status
from ..bse_integration.auth import BSEAuthenticator
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1",
    tags=["bse_auth"]
)

@router.post("/get_encrypted_password")
async def get_encrypted_password(
    bse_auth: BSEAuthenticator = Depends(),
    current_user = Depends(get_current_user)
):
    """
    Endpoint to get encrypted password from BSE for the authenticated user.
    """
    try:
        encrypted_password = await bse_auth.get_encrypted_password()
        if not encrypted_password:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get encrypted password"
            )
        return {"encrypted_password": encrypted_password}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
