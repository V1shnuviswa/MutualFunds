# /home/ubuntu/order_management_system/src/routers/registration.py

import logging
import random
import string
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from .. import crud, schemas
from ..database import get_db
from ..dependencies import get_current_user, get_bse_client_registrar
from ..bse_integration.client_registration import BSEClientRegistrar
from ..bse_integration.exceptions import BSEIntegrationError, BSEValidationError
from ..bse_integration.ucc_registration_template import create_ucc_template, map_client_to_bse_format
from ..models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Main registration router for step-by-step registration
router = APIRouter(
    prefix="/api/v1/registration",
    tags=["registration"],
    responses={404: {"description": "Not found"}}
)

# BSE client registration router
bse_router = APIRouter(
    prefix="/api/v1/bse/clients",
    tags=["bse_client_registration"],
    responses={404: {"description": "Not found"}}
)

def generate_internal_client_code() -> str:
    """Generate a unique client code for internal use"""
    prefix = "CLI"
    random_digits = ''.join(random.choice(string.digits) for _ in range(7))
    return f"{prefix}{random_digits}"

# ===== Internal Step-by-Step Registration Endpoints =====

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
    client_code = generate_internal_client_code()
    
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
    # Convert client_code to string to avoid type issues
    progress = crud.get_registration_progress(db, str(registration_state.client_code))
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
    import re

    # ✅ Validate PAN format if provided
    # Use getattr to safely check for attributes
    pan = getattr(step_data, 'pan', None)
    if pan and not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', pan.upper()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN format. Expected format: 5 letters, 4 digits, 1 letter (e.g., ABCDE1234F)"
        )

    # ✅ (optional) Validate email
    email = getattr(step_data, 'email', None)
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )

    # ✅ (optional) Validate mobile
    mobile = getattr(step_data, 'mobile', None)
    if mobile and not re.match(r'^[6-9]\d{9}$', mobile):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mobile number. It must be a 10-digit Indian number starting with 6-9"
        )

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
    current_user = Depends(get_current_user)
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
        # Get step data
        step1_data = json.loads(registration_state.step1_data) if registration_state.step1_data else {}
        step4_data = json.loads(registration_state.step4_data) if registration_state.step4_data else {}
        step5_data = json.loads(registration_state.step5_data) if registration_state.step5_data else {}
        step6_data = json.loads(registration_state.step6_data) if registration_state.step6_data else {}
        step7_data = json.loads(registration_state.step7_data) if registration_state.step7_data else {}
        step8_data = json.loads(registration_state.step8_data) if registration_state.step8_data else {}
        
        # Create client data dictionary with all required fields
        client_data = {}
        client_data["client_code"] = db_client.client_code
        client_data["client_name"] = db_client.client_name
        client_data["pan"] = db_client.pan
        client_data["tax_status"] = db_client.tax_status
        client_data["holding_type"] = db_client.holding_type

        # Add step data to client data
        client_data["email"] = step1_data.get("email", "")
        client_data["mobile"] = step1_data.get("mobile", "")
        client_data["date_of_birth"] = step4_data.get("date_of_birth", "")
        client_data["gender"] = step4_data.get("gender", "M")
        client_data["occupation"] = step4_data.get("occupation", "01")
        client_data["address"] = ", ".join(filter(None, [step5_data.get("flat_door_block"), step5_data.get("road_street")]))
        client_data["city"] = step5_data.get("city", "")
        client_data["state"] = step5_data.get("state", "")
        client_data["pincode"] = step5_data.get("pin_code", "")
        client_data["country"] = step5_data.get("country", "India")
        client_data["bank_account_number"] = step7_data.get("account_number", "")
        client_data["ifsc_code"] = step7_data.get("ifsc_code", "")
        client_data["account_type"] = step7_data.get("account_type", "SB")
        
        # Create BSE template
        bse_client_data = map_client_to_bse_format(client_data)
        
        # Initialize BSE client registrar
        bse_client_registrar = BSEClientRegistrar()
        
        # Register client with BSE
        response = await bse_client_registrar.register_client(bse_client_data)
        
        # Log the raw BSE response for debugging
        logger.info(f"BSE registration raw response: {response}")
        
        # Check response status
        if response.get("Status") == "0":
            logger.info(f"Registration completed successfully for client_code={client_code}")
            return db_client
        else:
            logger.error(f"BSE Registration failed for client_code={client_code}. Response: {response}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"BSE Registration failed: {response.get('Remarks', 'Unknown error')}"
            )
            
    except BSEValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"BSE Validation error: {str(e)}"
        )
    except BSEIntegrationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BSE Integration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
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
    
    # Validate token if provided - convert to string for comparison
    if session_token and str(registration_state.session_token) != session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )
    
    return registration_state

def _convert_to_bse_format(client: Any, registration_state: Any) -> Dict[str, Any]:
    """Convert client data to BSE format"""
    # Get step data
    step1_data = json.loads(registration_state.step1_data) if registration_state.step1_data else {}
    step4_data = json.loads(registration_state.step4_data) if registration_state.step4_data else {}
    step5_data = json.loads(registration_state.step5_data) if registration_state.step5_data else {}
    step6_data = json.loads(registration_state.step6_data) if registration_state.step6_data else {}
    step7_data = json.loads(registration_state.step7_data) if registration_state.step7_data else {}
    step8_data = json.loads(registration_state.step8_data) if registration_state.step8_data else {}
    
    # Format date of birth properly if it exists
    dob = None
    date_of_birth = step4_data.get("date_of_birth")
    if date_of_birth:
        try:
            # If it's a datetime object
            if hasattr(date_of_birth, 'isoformat'):
                dob = date_of_birth.isoformat()
            else:
                # If it's already a string
                dob = str(date_of_birth)
        except Exception:
            # Fallback
            dob = str(date_of_birth)
    
    # Create BSE format data
    return {
        "ClientCode": client.client_code,
        "PrimaryHolderFirstName": client.client_name.split()[0] if client.client_name else "",
        "PrimaryHolderLastName": client.client_name.split()[-1] if client.client_name and len(client.client_name.split()) > 1 else "",
        "TaxStatus": client.tax_status or "01",  # Default to Individual
        "PrimaryHolderPANExempt": "N",
        "PrimaryHolderPAN": client.pan,
        "Gender": step4_data.get("gender", "M"),  # Default to Male if not specified
        "DOB": dob,
        "OccupationCode": step4_data.get("occupation", "01"),  # Default to Business
        "HoldingNature": client.holding_type or "SI",  # Default to Single
        "ClientType": "P",  # Default to Physical
        "AccountType1": step7_data.get("account_type", "SB"),  # Default to Savings
        "AccountNo1": step7_data.get("account_number", ""),
        "IFSCCode1": step7_data.get("ifsc_code", ""),
        "DefaultBankFlag1": "Y",
        "DividendPayMode": "01",  # Default to Reinvest
        "Address1": ", ".join(filter(None, [step5_data.get("flat_door_block"), step5_data.get("road_street")])),
        "City": step5_data.get("city", ""),
        "State": step5_data.get("state", ""),
        "Pincode": step5_data.get("pin_code", ""),
        "Country": step5_data.get("country", "India"),
        "Email": step1_data.get("email", ""),
        "CommunicationMode": "E",  # Default to Email
        "IndianMobile": step1_data.get("mobile", ""),
        "PrimaryHolderKYCType": "K",  # Default to KYC
        "PaperlessFlag": "Z",  # Default to Paperless
    }

# ===== Direct BSE Client Registration Endpoints =====

class BSEClientRegistrationRequest(BaseModel):
    """Client registration request model with minimum required fields"""
    ClientCode: str = Field(..., description="Unique client code")
    PrimaryHolderFirstName: str = Field(..., description="First name of primary holder")
    PrimaryHolderLastName: str = Field("", description="Last name of primary holder")
    TaxStatus: str = Field(..., description="Tax status code")
    Gender: str = Field(..., description="Gender (M/F/O)")
    PrimaryHolderDOB: str = Field(..., description="Date of birth (DD/MM/YYYY)")
    OccupationCode: str = Field(..., description="Occupation code (01-10)")
    HoldingNature: str = Field(..., description="Holding nature (SI/JO/AS)")
    PrimaryHolderPANExempt: str = Field(..., description="PAN exempt flag (Y/N)")
    PrimaryHolderPAN: Optional[str] = Field(None, description="PAN number if not exempt")
    ClientType: str = Field(..., description="Client type (D/P)")
    DefaultDP: Optional[str] = Field(None, description="Default DP (CDSL/NSDL)")
    CDSLDPID: Optional[str] = Field(None, description="CDSL DP ID")
    CDSLCLTID: Optional[str] = Field(None, description="CDSL client ID")
    NSDLDPID: Optional[str] = Field(None, description="NSDL DP ID")
    NSDLCLTID: Optional[str] = Field(None, description="NSDL client ID")
    AccountType1: str = Field(..., description="Account type (SB/CB/NE/NO)")
    AccountNo1: str = Field(..., description="Account number")
    IFSCCode1: str = Field(..., description="IFSC code")
    DefaultBankFlag1: str = Field(..., description="Default bank flag (Y/N)")
    DividendPayMode: str = Field(..., description="Dividend pay mode")
    Address1: str = Field(..., description="Address line 1")
    City: str = Field(..., description="City")
    State: str = Field(..., description="State")
    Pincode: str = Field(..., description="Pincode")
    Country: str = Field(..., description="Country")
    Email: str = Field(..., description="Email address")
    CommunicationMode: str = Field(..., description="Communication mode (P/E/M)")
    IndianMobile: str = Field(..., description="Mobile number")
    PrimaryHolderKYCType: str = Field(..., description="KYC type (K/C/B/E)")
    PaperlessFlag: str = Field(..., description="Paperless flag (P/Z)")
    
    # Optional fields for second holder (required if HoldingNature is JO/AS)
    SecondHolderFirstName: Optional[str] = Field(None, description="First name of second holder")
    SecondHolderLastName: Optional[str] = Field(None, description="Last name of second holder")
    SecondHolderDOB: Optional[str] = Field(None, description="Date of birth of second holder (DD/MM/YYYY)")
    
    # Additional fields can be included as needed
    class Config:
        extra = "allow"  # Allow additional fields

class BSEClientRegistrationResponse(BaseModel):
    """Client registration response model"""
    status: str
    message: str
    client_code: str
    details: Optional[Dict[str, Any]] = None

@bse_router.post("/register", response_model=BSEClientRegistrationResponse)
async def bse_register_client(
    client_data: BSEClientRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new client with BSE STAR MF.
    
    This endpoint handles client registration using the BSE STAR MF API.
    """
    try:
        # Initialize BSE client registrar
        bse_client_registrar = BSEClientRegistrar()
        
        # Convert Pydantic model to dict
        client_dict = client_data.model_dump(exclude_none=False)
        
        # Log the client data for debugging
        logger.debug(f"Client registration data: {client_dict}")
        
        # Create a template with all 183 fields required by BSE
        bse_template = create_ucc_template(client_dict)
        
        # Validate mandatory fields
        for field in ["ClientCode", "PrimaryHolderFirstName", "TaxStatus", "Gender", 
                     "PrimaryHolderDOB", "OccupationCode", "HoldingNature", "PrimaryHolderPANExempt"]:
            if not bse_template.get(field):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate conditional fields
        if bse_template.get("PrimaryHolderPANExempt") == "N" and not bse_template.get("PrimaryHolderPAN"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PrimaryHolderPAN is required when PrimaryHolderPANExempt is N"
            )
            
        # Register client with BSE using the template
        response = await bse_client_registrar.register_client(bse_template)
        
        # Log the raw BSE response for debugging
        logger.info(f"BSE registration raw response: {response}")
        
        # Check response status
        if response.get("Status") == "0":
            # BSE registration successful
            db_client = None
            
            # Try to save client to database, but don't fail if database issues occur
            try:
                # Prepare client data
                client_name = f"{client_data.PrimaryHolderFirstName}"
                if client_data.PrimaryHolderLastName:
                    client_name += f" {client_data.PrimaryHolderLastName}"
                    
                # Check if client already exists
                existing_client = crud.get_client(db, client_data.ClientCode)
                if existing_client:
                    logger.info(f"Client {client_data.ClientCode} already exists, updating...")
                    # Update client
                    client_update = schemas.ClientCreate(
                        clientCode=client_data.ClientCode,
                        clientName=client_name,
                        pan=client_data.PrimaryHolderPAN if client_data.PrimaryHolderPANExempt == "N" else None,
                        kycStatus="Y" if client_data.PrimaryHolderKYCType in ["K", "C"] else "N",
                        accountType=client_data.ClientType,
                        holdingType=client_data.HoldingNature,
                        taxStatus=client_data.TaxStatus
                    )
                    db_client = crud.update_client(db, client_data.ClientCode, client_update)
                    logger.info(f"Client {client_data.ClientCode} updated in database")
                else:
                    # Create new client
                    client_create = schemas.ClientCreate(
                        clientCode=client_data.ClientCode,
                        clientName=client_name,
                        pan=client_data.PrimaryHolderPAN if client_data.PrimaryHolderPANExempt == "N" else None,
                        kycStatus="Y" if client_data.PrimaryHolderKYCType in ["K", "C"] else "N",
                        accountType=client_data.ClientType,
                        holdingType=client_data.HoldingNature,
                        taxStatus=client_data.TaxStatus
                    )
                    db_client = crud.create_client(db, client_create, current_user.id)
                    logger.info(f"Client {client_data.ClientCode} created in database")
            except Exception as db_error:
                # Log database error but continue with success response
                logger.error(f"Failed to save client to database: {db_error}", exc_info=True)
                logger.info(f"Client {client_data.ClientCode} registered with BSE but not saved to database")
            
            # Return success response even if database save failed
            return BSEClientRegistrationResponse(
                status="success",
                message=response.get("Remarks", "Client registered successfully"),
                client_code=client_data.ClientCode,
                details=response
            )
        else:
            # Log detailed error
            logger.error(f"BSE registration failed with status {response.get('Status')}: {response.get('Remarks')}")
            raise BSEIntegrationError(response.get("Remarks", "Unknown error"))
            
    except BSEValidationError as e:
        logger.error(f"Client registration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BSEIntegrationError as e:
        logger.error(f"Client registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Changed from 500 to 400 for client-side errors
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during client registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@bse_router.post("/update", response_model=BSEClientRegistrationResponse)
async def bse_update_client(
    client_data: BSEClientRegistrationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing client with BSE STAR MF.
    
    This endpoint handles client update using the BSE STAR MF API.
    """
    try:
        # Initialize BSE client registrar
        bse_client_registrar = BSEClientRegistrar()
        
        # Convert Pydantic model to dict
        client_dict = client_data.model_dump(exclude_none=False)
        
        # Update client
        response = await bse_client_registrar.update_client(client_dict)
        
        # Check response status
        if response.get("Status") == "0":
            return BSEClientRegistrationResponse(
                status="success",
                message=response.get("Remarks", "Client updated successfully"),
                client_code=client_data.ClientCode,
                details=response
            )
        else:
            raise BSEIntegrationError(response.get("Remarks", "Unknown error"))
            
    except BSEValidationError as e:
        logger.error(f"Client update validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BSEIntegrationError as e:
        logger.error(f"Client update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@bse_router.post("/generate-code", response_model=Dict[str, str])
async def bse_generate_client_code(
    client_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Generate a client code based on name and DOB.
    
    This endpoint generates a unique client code using the BSE format.
    """
    try:
        # Initialize BSE client registrar
        bse_client_registrar = BSEClientRegistrar()
        
        # Generate client code
        client_code = bse_client_registrar.create_client_code(client_data)
        
        return {"client_code": client_code}
    except Exception as e:
        logger.error(f"Error generating client code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating client code: {str(e)}"
        ) 