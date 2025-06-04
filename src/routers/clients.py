from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_active_user, get_bse_client_registrar
from ..bse_integration.client_registration import BSEClientRegistrar
from ..bse_integration.exceptions import BSEClientRegError, BSETransportError

router = APIRouter(
    prefix="/api/v1/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)

@router.post("/register", response_model=schemas.Client)
async def register_client(
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
    bse_client_registrar: BSEClientRegistrar = Depends(get_bse_client_registrar)
):
    """
    Register a new client both in local database and with BSE.
    """
    # First check if client already exists
    if crud.get_client(db, client_code=client_data.client_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client already registered"
        )
    
    try:
        # Register with BSE first
        bse_response = bse_client_registrar.register_client(client_data.model_dump(by_alias=True))
        
        # If BSE registration successful, store in local database
        if bse_response.get("Status") == "1":  # Assuming "1" means success
            db_client = crud.create_client(db=db, client=client_data, user_id=current_user.id)
            return db_client
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BSE Registration failed: {bse_response.get('Message', 'Unknown error')}"
            )
            
    except BSETransportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"BSE service unavailable: {str(e)}"
        )
    except BSEClientRegError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BSE Registration error: {str(e)}"
        )

@router.put("/{client_code}", response_model=schemas.Client)
async def update_client(
    client_code: str,
    client_data: schemas.ClientCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user),
    bse_client_registrar: BSEClientRegistrar = Depends(get_bse_client_registrar)
):
    """
    Update client details both in local database and with BSE.
    """
    # Check if client exists
    db_client = crud.get_client(db, client_code=client_code)
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    try:
        # Update with BSE first
        bse_response = bse_client_registrar.update_client(client_data.model_dump(by_alias=True))
        
        # If BSE update successful, update local database
        if bse_response.get("Status") == "1":  # Assuming "1" means success
            updated_client = crud.update_client(
                db=db,
                client_code=client_code,
                client_data=client_data
            )
            return updated_client
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BSE Update failed: {bse_response.get('Message', 'Unknown error')}"
            )
            
    except BSETransportError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"BSE service unavailable: {str(e)}"
        )
    except BSEClientRegError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BSE Update error: {str(e)}"
        )

@router.get("/{client_code}", response_model=schemas.Client)
async def get_client(
    client_code: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_user)
):
    """
    Get client details from local database.
    """
    db_client = crud.get_client(db, client_code=client_code)
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    return db_client 