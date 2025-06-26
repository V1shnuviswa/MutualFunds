# /home/ubuntu/order_management_system/src/crud.py

from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import secrets
from sqlalchemy import select, update, func, and_, or_, desc
from sqlalchemy.orm import Session, selectinload
from . import models, schemas, security

# --- User CRUD --- #

def get_user(db: Session, user_id: int):
    return db.get(models.User, user_id)

def get_user_by_userid(db: Session, user_id: str):
    return db.execute(select(models.User).filter(models.User.user_id == user_id)).scalar_one_or_none()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        user_id=user.user_id,
        member_id=user.member_id,
        password_hash=hashed_password,
        pass_key=user.pass_key # Consider hashing/encrypting passkey if sensitive
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Client CRUD --- #

def get_client(db: Session, client_code: str):
    return db.get(models.Client, client_code)

def create_client(db: Session, client: schemas.ClientCreate, user_id: int):
    db_client = models.Client(**client.model_dump(), created_by_user_id=user_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def update_client(db: Session, client_code: str, client_data: schemas.ClientCreate):
    db_client = get_client(db, client_code=client_code)
    if db_client:
        for key, value in client_data.model_dump(exclude_unset=True).items():
            setattr(db_client, key, value)
    db.commit()
    db.refresh(db_client)
    return db_client

# --- Scheme CRUD --- #

def get_scheme(db: Session, scheme_code: str):
    return db.get(models.Scheme, scheme_code)

def create_scheme(db: Session, scheme: schemas.SchemeCreate):
    db_scheme = models.Scheme(**scheme.model_dump())
    db.add(db_scheme)
    db.commit()
    db.refresh(db_scheme)
    return db_scheme

# --- Order CRUD --- #

def create_lumpsum_order(db: Session, order_data: dict, user_id: int):
    # Map BSE field names to database field names
    
    # Convert euin_declared to 'Y'/'N' string if it's a boolean
    euin_flag = order_data.get("EUINFlag")
    if isinstance(euin_flag, bool):
        euin_declared = 'Y' if euin_flag else 'N'
    else:
        euin_declared = euin_flag if euin_flag in ['Y', 'N'] else 'N'
    
    db_order = models.Order(
        unique_ref_no=order_data.get("RefNo"),
        client_code=order_data.get("ClientCode"),
        scheme_code=order_data.get("SchemeCd"),
        order_type="LUMPSUM",
        transaction_type="PURCHASE" if order_data.get("BuySell") == "P" else "REDEMPTION",
        amount=order_data.get("Amount"),
        quantity=order_data.get("Qty"),
        folio_no=order_data.get("FolioNo"),
        status="RECEIVED",
        user_id=user_id,
        ip_address=order_data.get("IPAdd"),
        euin=order_data.get("EUIN"),
        euin_declared=euin_declared,  # Use the converted string value
        sub_arn_code=order_data.get("SubBrokerARN"),
        dp_txn_mode=order_data.get("DPTxn"),
        status_message=order_data.get("Remarks")
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def create_sip_registration_order(db: Session, sip_data: schemas.SIPOrderCreate, user_id: int):
    # Create the initial order record
    
    # Convert euin_declaration to 'Y'/'N' string if it's a boolean
    if isinstance(sip_data.euin_declaration, bool):
        euin_declared = 'Y' if sip_data.euin_declaration else 'N'
    else:
        euin_declared = sip_data.euin_declaration if sip_data.euin_declaration in ['Y', 'N'] else 'N'
    
    db_order = models.Order(
        unique_ref_no=sip_data.unique_ref_no,
        client_code=sip_data.client_code,
        scheme_code=sip_data.scheme_code,
        order_type="SIP_REG",
        transaction_type="PURCHASE", # SIP is typically purchase
        amount=sip_data.installment_amount,  # Fixed: use installment_amount instead of amount
        folio_no=sip_data.folio_no,
        status="RECEIVED", # Initial status for registration order
        user_id=user_id,
        ip_address=sip_data.ip_address,
        euin=sip_data.euin,
        euin_declared=euin_declared,  # Use the converted string value
        sub_arn_code=sip_data.sub_broker_arn  # Fixed: use sub_broker_arn instead of sub_arn_code
        # Add other fields like brokerage, remarks if stored in DB
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create the SIP registration record linked to the order
    db_sip = models.SIPRegistration(
        order_id=db_order.id,
        client_code=sip_data.client_code,
        scheme_code=sip_data.scheme_code,
        frequency=sip_data.frequency_type.value,  # Fixed: use frequency_type.value
        amount=sip_data.installment_amount,  # Fixed: use installment_amount instead of amount
        installments=sip_data.no_of_installments,  # Fixed: use no_of_installments instead of installments
        start_date=sip_data.start_date,  # Fixed: use start_date instead of startDate
        end_date=None,  # Calculate end date based on start_date and installments if needed
        mandate_id=sip_data.mandate_id,  # Fixed: use mandate_id instead of mandateId
        first_order_today="Y" if sip_data.first_order_today else "N",  # Fixed: convert boolean to Y/N
        status="REGISTERED" # Initial SIP status
    )
    db.add(db_sip)
    db.commit()
    db.refresh(db_sip)
    # Return both? Or just the order? API expects SIP Reg ID eventually.
    # For now, return the order, SIP details are linked.
    return db_order

def get_order_by_ref_no(db: Session, unique_ref_no: str):
    return db.execute(select(models.Order).filter(models.Order.unique_ref_no == unique_ref_no)).scalar_one_or_none()

def get_orders_by_status_query(db: Session, query_params: schemas.OrderStatusQuery):
    stmt = select(models.Order).where(
        models.Order.client_code == query_params.clientCode,
        models.Order.order_timestamp >= query_params.fromDate, # Assuming order_timestamp date part
        models.Order.order_timestamp <= query_params.toDate # Assuming order_timestamp date part
        # Add memberId check if necessary (e.g., check order.user.member_id)
    )
    if query_params.orderId:
        stmt = stmt.where(models.Order.order_id_bse == query_params.orderId)
    if query_params.status:
        stmt = stmt.where(models.Order.status == query_params.status)

    # Add joins to fetch related data if needed for response (client name, scheme name)
    stmt = stmt.options(
        selectinload(models.Order.client),
        selectinload(models.Order.scheme)
    )

    orders = db.execute(stmt).scalars().all()
    return orders

def update_order_status(
    db: Session,
    order_id: int,
    status: str,
    user_id: int,
    status_code: str | None = None,
    remarks: str | None = None,
    payment_status: str | None = None,
    payment_reference: str | None = None,
    payment_date: datetime | None = None,
    allotment_date: datetime | None = None,
    allotment_nav: Decimal | None = None,
    units_allotted: Decimal | None = None,
    settlement_date: datetime | None = None,
    settlement_amount: Decimal | None = None,
    order_id_bse: str | None = None
) -> models.Order:
    """
    Update order status and create status history record.
    """
    db_order = db.get(models.Order, order_id)
    if not db_order:
        raise ValueError(f"Order {order_id} not found")

    # Update order status fields
    db_order.status = status
    db_order.status_code = status_code
    db_order.status_updated_by = user_id
    db_order.status_updated_at = datetime.utcnow()

    # Update BSE order ID if provided
    if order_id_bse:
        db_order.order_id_bse = order_id_bse

    # Update optional fields if provided
    if payment_status:
        db_order.payment_status = payment_status
    if payment_reference:
        db_order.payment_reference = payment_reference
    if payment_date:
        db_order.payment_date = payment_date
    if allotment_date:
        db_order.allotment_date = allotment_date
    if allotment_nav:
        db_order.allotment_nav = allotment_nav
    if units_allotted:
        db_order.units_allotted = units_allotted
    if settlement_date:
        db_order.settlement_date = settlement_date
    if settlement_amount:
        db_order.settlement_amount = settlement_amount

    # Create status history record
    status_history = models.OrderStatusHistory(
        order_id=order_id,
        status=status,
        remarks=remarks,
        created_by=user_id
    )
    db.add(status_history)

    try:
        db.commit()
        db.refresh(db_order)
        return db_order
    except Exception as e:
        db.rollback()
        raise e

def get_order_status_history(
    db: Session,
    order_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[models.OrderStatusHistory]:
    """
    Get status history for an order.
    """
    return db.query(models.OrderStatusHistory)\
        .filter(models.OrderStatusHistory.order_id == order_id)\
        .order_by(models.OrderStatusHistory.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def update_sip_status(db: Session, sip_reg_id: int, bse_sip_reg_id: str, status: str):
    stmt = (
        update(models.SIPRegistration)
        .where(models.SIPRegistration.id == sip_reg_id)
        .values(
            sip_reg_id_bse=bse_sip_reg_id,
            status=status
        )
    )
    db.execute(stmt)
    db.commit()

# --- Mandate CRUD (Placeholder) --- #

def get_mandate(db: Session, mandate_id: str) -> Optional[models.Mandate]:
    """
    Get a mandate by its ID.
    """
    return db.execute(
        select(models.Mandate)
        .filter(models.Mandate.mandate_id == mandate_id)
    ).scalar_one_or_none()

def create_mandate(db: Session, mandate: schemas.MandateCreate) -> models.Mandate:
    """
    Create a new mandate.
    """
    db_mandate = models.Mandate(**mandate.model_dump())
    db.add(db_mandate)
    db.commit()
    db.refresh(db_mandate)
    return db_mandate

def get_order_by_payment_reference(db: Session, payment_reference: str) -> Optional[models.Order]:
    """
    Get an order by its payment reference.
    """
    return db.execute(
        select(models.Order)
        .filter(models.Order.payment_reference == payment_reference)
    ).scalar_one_or_none()

def get_order(db: Session, order_id: int) -> Optional[models.Order]:
    """
    Get an order by its ID.
    """
    return db.get(models.Order, order_id)

# --- Client Registration State CRUD Operations --- #

def create_registration_state(db: Session, client_code: str, user_id: int) -> models.ClientRegistrationState:
    """Create a new registration state for a client"""
    # Generate a secure token for session resumption
    token = secrets.token_urlsafe(32)
    token_expiry = datetime.now() + timedelta(days=7)  # Token valid for 7 days
    
    db_registration = models.ClientRegistrationState(
        client_code=client_code,
        current_step=1,
        is_complete=False,
        session_token=token,
        token_expiry=token_expiry,
        created_by_user_id=user_id
    )
    
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return db_registration

def get_registration_state(db: Session, client_code: str) -> models.ClientRegistrationState:
    """Get registration state by client code"""
    return db.query(models.ClientRegistrationState).filter(
        models.ClientRegistrationState.client_code == client_code
    ).first()

def get_registration_state_by_token(db: Session, token: str) -> models.ClientRegistrationState:
    """Get registration state by session token"""
    return db.query(models.ClientRegistrationState).filter(
        models.ClientRegistrationState.session_token == token,
        models.ClientRegistrationState.token_expiry > datetime.now()
    ).first()

def update_registration_step(
    db: Session, 
    client_code: str, 
    step: int, 
    step_data: dict
) -> models.ClientRegistrationState:
    """Update registration state for a specific step"""
    db_registration = get_registration_state(db, client_code)
    
    if not db_registration:
        return None
    
    # Update step data
    step_data_column = f"step{step}_data"
    step_complete_column = f"step{step}_complete"
    
    setattr(db_registration, step_data_column, json.dumps(step_data))
    setattr(db_registration, step_complete_column, True)
    
    # Update current step if moving forward
    if db_registration.current_step == step:
        db_registration.current_step = step + 1
    
    # Check if all steps are complete
    all_steps_complete = all([
        db_registration.step1_complete,
        db_registration.step2_complete,
        db_registration.step3_complete,
        db_registration.step4_complete,
        db_registration.step5_complete,
        db_registration.step6_complete,
        db_registration.step7_complete,
        db_registration.step8_complete,
        db_registration.step9_complete
    ])
    
    if all_steps_complete:
        db_registration.is_complete = True
    
    db.commit()
    db.refresh(db_registration)
    return db_registration

def complete_registration(db: Session, client_code: str) -> models.Client:
    """
    Complete the registration process by consolidating all step data
    and creating/updating the final Client record
    """
    db_registration = get_registration_state(db, client_code)
    
    if not db_registration or not db_registration.is_complete:
        return None
    
    # Parse JSON data from each step
    step1_data = json.loads(db_registration.step1_data) if db_registration.step1_data else {}
    step2_data = json.loads(db_registration.step2_data) if db_registration.step2_data else {}
    step3_data = json.loads(db_registration.step3_data) if db_registration.step3_data else {}
    step4_data = json.loads(db_registration.step4_data) if db_registration.step4_data else {}
    step5_data = json.loads(db_registration.step5_data) if db_registration.step5_data else {}
    step6_data = json.loads(db_registration.step6_data) if db_registration.step6_data else {}
    step7_data = json.loads(db_registration.step7_data) if db_registration.step7_data else {}
    step8_data = json.loads(db_registration.step8_data) if db_registration.step8_data else {}
    
    # Check if client already exists
    db_client = get_client(db, client_code=client_code)
    
    if db_client:
        # Update existing client
        db_client.client_name = step1_data.get("client_name")
        db_client.pan = step4_data.get("pan")
        db_client.kyc_status = "Y"  # Assume KYC is completed through this process
        db_client.account_type = step1_data.get("investment_mode")
        db_client.holding_type = step1_data.get("investment_mode")
        db_client.tax_status = step4_data.get("tax_status")
        db_client.updated_at = datetime.now()
    else:
        # Create new client
        db_client = models.Client(
            client_code=client_code,
            client_name=step1_data.get("client_name"),
            pan=step4_data.get("pan"),
            kyc_status="Y",  # Assume KYC is completed through this process
            account_type=step1_data.get("investment_mode"),
            holding_type=step1_data.get("investment_mode"),
            tax_status=step4_data.get("tax_status"),
            created_by_user_id=db_registration.created_by_user_id
        )
        db.add(db_client)
    
    # Additional client details could be stored in a related table if needed
    
    db.commit()
    db.refresh(db_client)
    return db_client

def get_registration_progress(db: Session, client_code: str) -> dict:
    """Get registration progress status"""
    db_registration = get_registration_state(db, client_code)
    
    if not db_registration:
        return None
    
    steps_completed = []
    if db_registration.step1_complete:
        steps_completed.append(1)
    if db_registration.step2_complete:
        steps_completed.append(2)
    if db_registration.step3_complete:
        steps_completed.append(3)
    if db_registration.step4_complete:
        steps_completed.append(4)
    if db_registration.step5_complete:
        steps_completed.append(5)
    if db_registration.step6_complete:
        steps_completed.append(6)
    if db_registration.step7_complete:
        steps_completed.append(7)
    if db_registration.step8_complete:
        steps_completed.append(8)
    if db_registration.step9_complete:
        steps_completed.append(9)
    
    # Determine next step URL
    base_url = "/api/v1/registration"
    next_step = db_registration.current_step
    next_step_url = f"{base_url}/step/{next_step}"
    
    if db_registration.is_complete:
        next_step_url = f"{base_url}/complete"
    
    return {
        "client_code": db_registration.client_code,
        "current_step": db_registration.current_step,
        "is_complete": db_registration.is_complete,
        "session_token": db_registration.session_token,
        "steps_completed": steps_completed,
        "next_step_url": next_step_url
    }

def get_filtered_orders(
    db: Session,
    client_code: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    order_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Order]:
    """
    Get filtered orders based on various criteria.
    """
    stmt = select(models.Order)
    
    # Apply filters
    if client_code:
        stmt = stmt.where(models.Order.client_code == client_code)
    
    if from_date:
        stmt = stmt.where(models.Order.order_timestamp >= from_date)
    
    if to_date:
        # Add one day to include the entire to_date
        to_date_end = datetime.combine(to_date, datetime.max.time())
        stmt = stmt.where(models.Order.order_timestamp <= to_date_end)
    
    if order_type:
        stmt = stmt.where(models.Order.order_type == order_type)
    
    if status:
        stmt = stmt.where(models.Order.status == status)
    
    # Add joins to fetch related data
    stmt = stmt.options(
        selectinload(models.Order.client),
        selectinload(models.Order.scheme)
    )
    
    # Order by timestamp descending (most recent first)
    stmt = stmt.order_by(models.Order.order_timestamp.desc())
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    
    orders = db.execute(stmt).scalars().all()
    return orders

def get_orders_by_client(
    db: Session,
    client_code: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Order]:
    """
    Get all orders for a specific client.
    """
    return get_filtered_orders(
        db=db,
        client_code=client_code,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )

