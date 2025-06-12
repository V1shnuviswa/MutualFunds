# /home/ubuntu/order_management_system/src/routers/registration.py

import logging
import random
import string
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Header

from sqlalchemy.orm import Session
from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, get_bse_client_registrar
from ..bse_integration.client_registration import BSEClientRegistrar
from ..bse_integration.exceptions import BSEClientRegError, BSETransportError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/registration",
    tags=["registration"],
    responses={404: {"description": "Not found"}}
)

def generate_client_code() -> str:
    """Generate a unique client code"""
    prefix = "CLI"
    random_digits = ''.join(random.choice(string.digits) for _ in range(7))
    return f"{prefix}{random_digits}"

@router.post("/start", response_model=schemas.RegistrationStateResponse)
async def start_registration(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start a new client registration process.
    Returns a session token that should be used for subsequent steps.
    """
    # Generate a unique client code
    client_code = generate_client_code()
    
    # Create registration state
    registration_state = crud.create_registration_state(
        db=db, 
        client_code=client_code, 
        user_id=current_user.id
    )
    
    # Return registration state
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.get("/resume/{token}", response_model=schemas.RegistrationStateResponse)
async def resume_registration(
    token: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Resume an existing registration process using a session token.
    """
    # Get registration state by token
    registration_state = crud.get_registration_state_by_token(db, token)
    
    if not registration_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration session not found or expired"
        )
    
    # Return registration progress
    progress = crud.get_registration_progress(db, registration_state.client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/1", response_model=schemas.RegistrationStateResponse)
async def process_step1(
    step_data: schemas.RegistrationStep1,
    client_code: str = Query(..., description="Client code from registration start"),
    session_token: Optional[str] = Header(None, description="Session token from registration start"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 1: Personal details & investment mode
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=1,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/2", response_model=schemas.RegistrationStateResponse)
async def process_step2(
    step_data: schemas.RegistrationStep2,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 2: Investment type preferences
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step1_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=2,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/3", response_model=schemas.RegistrationStateResponse)
async def process_step3(
    step_data: schemas.RegistrationStep3,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 3: Scheme selection
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step2_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Validate scheme code
    scheme = crud.get_scheme(db, scheme_code=step_data.scheme_code)
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid scheme code"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=3,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress with NAV and processing information
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/4", response_model=schemas.RegistrationStateResponse)
async def process_step4(
    step_data: schemas.RegistrationStep4,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 4: Detailed personal information
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step3_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=4,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/5", response_model=schemas.RegistrationStateResponse)
async def process_step5(
    step_data: schemas.RegistrationStep5,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 5: Address details
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step4_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=5,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/6", response_model=schemas.RegistrationStateResponse)
async def process_step6(
    step_data: schemas.RegistrationStep6,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 6: Tax residency declaration
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step5_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=6,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/7", response_model=schemas.RegistrationStateResponse)
async def process_step7(
    step_data: schemas.RegistrationStep7,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 7: Investment & bank details
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step6_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Validate account number confirmation
    if step_data.account_number != step_data.confirm_account_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account number and confirmation do not match"
        )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=7,
        step_data=step_data.model_dump()
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/step/8", response_model=schemas.RegistrationStateResponse)
async def process_step8(
    step_data: schemas.RegistrationStep8,
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process Step 8: Nominee details
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if previous step is complete
    if not registration_state.step7_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Previous step must be completed first"
        )
    
    # Validate nominee details if not opted out
    if not step_data.nominee_opt_out:
        if not step_data.nominee_name or not step_data.nominee_relation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nominee details required when not opting out"
            )
    
    # Update registration state with step data
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=8,
        step_data=step_data.model_dump()
    )
    
    # Also mark step 9 as complete since mobile verification is handled separately
    updated_state = crud.update_registration_step(
        db=db,
        client_code=client_code,
        step=9,
        step_data={}
    )
    
    # Return updated progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

@router.post("/complete", response_model=schemas.Client)
async def complete_registration(
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    bse_client_registrar: BSEClientRegistrar = Depends(get_bse_client_registrar)
):
    """
    Complete the registration process and create/update client in BSE.
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Check if all steps are complete
    if not registration_state.is_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All steps must be completed first"
        )
    
    # Complete registration and get client data
    db_client = crud.complete_registration(db, client_code)
    
    if not db_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete registration"
        )
    
    # Register client with BSE
    try:
        # Convert client data to BSE format
        bse_client_data = _convert_to_bse_format(db_client, registration_state)
        
        # Register with BSE
        bse_response = await bse_client_registrar.register_client(bse_client_data)
        
        # Check BSE response
        if bse_response.get("Status") == "1":  # Assuming "1" means success
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

@router.get("/status", response_model=schemas.RegistrationStateResponse)
async def get_registration_status(
    client_code: str = Query(...),
    session_token: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get the current status of registration process.
    """
    # Validate registration state
    registration_state = _validate_registration_session(db, client_code, session_token)
    
    # Return registration progress
    progress = crud.get_registration_progress(db, client_code)
    return schemas.RegistrationStateResponse(**progress)

# Helper functions
def _validate_registration_session(db: Session, client_code: str, session_token: Optional[str]) -> Any:
    """Validate registration session"""
    # Try to get registration state by client code first
    registration_state = crud.get_registration_state(db, client_code)
    
    # If not found, try by token
    if not registration_state and session_token:
        registration_state = crud.get_registration_state_by_token(db, session_token)
    
    if not registration_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration session not found"
        )
    
    # Validate token if provided
    if session_token and registration_state.session_token != session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    return registration_state

def _convert_to_bse_format(client: Any, registration_state: Any) -> Dict[str, Any]:
    """Convert client data to BSE format"""
    # This would need to be customized based on BSE's specific requirements
    # Here's a placeholder implementation
    
    # Get step data
    step1_data = json.loads(registration_state.step1_data) if registration_state.step1_data else {}
    step4_data = json.loads(registration_state.step4_data) if registration_state.step4_data else {}
    step5_data = json.loads(registration_state.step5_data) if registration_state.step5_data else {}
    step6_data = json.loads(registration_state.step6_data) if registration_state.step6_data else {}
    step7_data = json.loads(registration_state.step7_data) if registration_state.step7_data else {}
    step8_data = json.loads(registration_state.step8_data) if registration_state.step8_data else {}
    
    return {
        "ClientCode": client.client_code,
        "ClientName": client.client_name,
        "PAN": client.pan,
        "KYCStatus": client.kyc_status,
        "AccountType": client.account_type,
        "HoldingType": client.holding_type,
        "TaxStatus": client.tax_status,
        # Add other fields as needed for BSE
        "Email": step1_data.get("email"),
        "Mobile": step1_data.get("mobile"),
        "DateOfBirth": step4_data.get("date_of_birth").isoformat() if step4_data.get("date_of_birth") else None,
        "Gender": step4_data.get("gender"),
        "Occupation": step4_data.get("occupation"),
        "Address": f"{step5_data.get('flat_door_block')}, {step5_data.get('road_street')}, {step5_data.get('area_locality')}",
        "City": step5_data.get("city"),
        "State": step5_data.get("state"),
        "Country": step5_data.get("country"),
        "Pincode": step5_data.get("pin_code"),
        "BankName": step7_data.get("bank_name"),
        "AccountNumber": step7_data.get("account_number"),
        "IFSCCode": step7_data.get("ifsc_code"),
        "AccountType": step7_data.get("account_type"),
        "NomineeName": step8_data.get("nominee_name") if not step8_data.get("nominee_opt_out") else None,
        "NomineeRelation": step8_data.get("nominee_relation") if not step8_data.get("nominee_opt_out") else None,
    } 