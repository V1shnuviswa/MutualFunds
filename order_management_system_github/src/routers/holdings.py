# /home/ubuntu/order_management_system/src/routers/holdings.py

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..dependencies import (
    DbDependency, CurrentUserDependency,
    get_bse_authenticator, get_bse_order_placer
)
from ..bse_integration.exceptions import (
    BSEIntegrationError, BSEAuthError, BSESoapFault, BSETransportError, BSEValidationError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["holdings"],
)

@router.get("/holdings", response_model=List[schemas.HoldingResponse])
async def get_holdings(
    client_code: Optional[str] = None,
    folio_no: Optional[str] = None,
    scheme_code: Optional[str] = None,
    db: Session = Depends(DbDependency),
    current_user: schemas.User = Depends(CurrentUserDependency),
    bse_authenticator = Depends(get_bse_authenticator),
    bse_order_placer = Depends(get_bse_order_placer)
):
    """
    Retrieve mutual fund holdings in the user's DEMAT.
    """
    try:
        # Get encrypted password for BSE authentication
        encrypted_password = await bse_authenticator.get_encrypted_password()
        
        # Fetch holdings from BSE
        # This is a placeholder - you would need to implement the actual BSE API call
        # bse_response = await bse_order_placer.get_holdings(
        #     client_code=client_code,
        #     folio_no=folio_no,
        #     scheme_code=scheme_code,
        #     encrypted_password=encrypted_password
        # )
        
        # For now, let's return mock data
        mock_holdings = [
            schemas.HoldingResponse(
                clientCode=client_code or "CLIENT001",
                folioNo="1234567890",
                schemeCode="BSE123",
                schemeName="ABC Mutual Fund - Growth",
                isin="INF123A01234",
                units=100.5678,
                navValue=25.4321,
                currentValue=2557.45,
                purchaseValue=2000.00,
                purchaseDate="2023-01-15",
                gainLoss=557.45,
                gainLossPercentage=27.87
            ),
            schemas.HoldingResponse(
                clientCode=client_code or "CLIENT001",
                folioNo="1234567891",
                schemeCode="BSE456",
                schemeName="XYZ Equity Fund - Dividend",
                isin="INF456B05678",
                units=50.1234,
                navValue=35.6789,
                currentValue=1788.23,
                purchaseValue=1500.00,
                purchaseDate="2023-02-20",
                gainLoss=288.23,
                gainLossPercentage=19.22
            )
        ]
        
        return mock_holdings
        
    except (BSEAuthError, BSEValidationError, BSESoapFault, BSETransportError) as e:
        logger.error(f"BSE Integration Error retrieving holdings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BSEValidationError) else status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving holdings: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve holdings: {str(e)}"
        )

@router.get("/instruments", response_model=List[schemas.InstrumentResponse])
async def get_instruments(
    amc_code: Optional[str] = None,
    scheme_type: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(DbDependency),
    current_user: schemas.User = Depends(CurrentUserDependency)
):
    """
    Fetch a master list of available funds.
    """
    try:
        # Get schemes from database
        schemes = crud.get_schemes(
            db=db,
            amc_code=amc_code,
            category=category,
            search=search,
            limit=limit,
            offset=offset
        )
        
        # Map to response schema
        response_data = []
        for scheme in schemes:
            instrument = schemas.InstrumentResponse(
                schemeCode=scheme.scheme_code,
                schemeName=scheme.scheme_name,
                amcCode=scheme.amc_code,
                rtaCode=scheme.rta_code,
                isin=scheme.isin,
                category=scheme.category,
                isActive=scheme.is_active,
                minInvestment=1000.00,  # Default value, should come from scheme details
                sipMinimum=500.00,      # Default value, should come from scheme details
                purchaseAllowed=True,   # Default value, should come from scheme details
                redemptionAllowed=True, # Default value, should come from scheme details
                sipAllowed=True,        # Default value, should come from scheme details
                switchAllowed=True      # Default value, should come from scheme details
            )
            response_data.append(instrument)
            
        return response_data
        
    except Exception as e:
        logger.error(f"Error retrieving instruments: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve instruments: {str(e)}"
        )

@router.get("/instruments/{scheme_code}", response_model=schemas.InstrumentDetailResponse)
async def get_instrument_details(
    scheme_code: str,
    db: Session = Depends(DbDependency),
    current_user: schemas.User = Depends(CurrentUserDependency)
):
    """
    Fetch detailed information about a specific instrument/scheme.
    """
    try:
        # Get scheme from database
        scheme = crud.get_scheme(db=db, scheme_code=scheme_code)
        if not scheme:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheme not found"
            )
            
        # Map to response schema
        return schemas.InstrumentDetailResponse(
            schemeCode=scheme.scheme_code,
            schemeName=scheme.scheme_name,
            amcCode=scheme.amc_code,
            amcName="AMC Name",  # Should come from AMC details
            rtaCode=scheme.rta_code,
            rtaName="RTA Name",  # Should come from RTA details
            isin=scheme.isin,
            category=scheme.category,
            subCategory="Equity Large Cap",  # Should come from scheme details
            isActive=scheme.is_active,
            minInvestment=1000.00,
            sipMinimum=500.00,
            purchaseAllowed=True,
            redemptionAllowed=True,
            sipAllowed=True,
            switchAllowed=True,
            exitLoad="1% if redeemed within 365 days",  # Should come from scheme details
            expenseRatio=1.25,  # Should come from scheme details
            fundManager="Fund Manager Name",  # Should come from scheme details
            launchDate="2010-01-01",  # Should come from scheme details
            fundSize=1000000000.00,  # Should come from scheme details
            nav=25.4321,  # Should come from latest NAV
            navDate="2023-05-01",  # Should come from latest NAV
            riskCategory="Moderate",  # Should come from scheme details
            benchmark="NIFTY 50",  # Should come from scheme details
            settlementDays=3  # Should come from scheme details
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving instrument details: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve instrument details: {str(e)}"
        ) 