# /home/ubuntu/order_management_system/src/schemas.py

from pydantic import BaseModel, Field, EmailStr, validator, field_validator, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
import decimal
from enum import Enum

# --- Enums --- #
class OrderType(str, Enum):
    LUMPSUM = "LUMPSUM"
    SIP = "SIP"
    XSIP = "XSIP"
    SWITCH = "SWITCH"
    SPREAD = "SPREAD"

class TransactionType(str, Enum):
    PURCHASE = "P"
    REDEMPTION = "R"
    SWITCH_OUT = "SO"
    SWITCH_IN = "SI"

class DPTxnMode(str, Enum):
    CDSL = "C"
    NSDL = "N"
    PHYSICAL = "P"

class BuySellType(str, Enum):
    FRESH = "FRESH"
    ADDITIONAL = "ADDITIONAL"

class OrderStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PENDING = "PENDING"
    PAYMENT_INITIATED = "PAYMENT_INITIATED"
    PAYMENT_COMPLETED = "PAYMENT_COMPLETED"
    SENT_TO_BSE = "SENT_TO_BSE"
    ACCEPTED_BY_BSE = "ACCEPTED_BY_BSE"
    REJECTED_BY_BSE = "REJECTED_BY_BSE"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class SIPFrequency(str, Enum):
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    WEEKLY = "WEEKLY"

# --- Base Models --- #
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- User Schemas --- #
class UserBase(BaseModel):
    user_id: str = Field(..., max_length=50)
    member_id: str = Field(..., max_length=50)
    pass_key: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    userId: str = Field(..., alias="userId")
    memberId: str = Field(..., alias="memberId")
    password: str
    passKey: Optional[str] = Field(None, alias="passKey")

class UserInDBBase(UserBase):
    # Pydantic V2 model_config for ORM mode
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class User(UserInDBBase):
    pass

# --- Client Schemas --- #
class ClientBase(BaseModel):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    client_code: str = Field(..., max_length=50, alias="clientCode")
    client_name: Optional[str] = Field(None, max_length=255, alias="clientName")
    pan: Optional[str] = Field(None, max_length=10)
    kyc_status: Literal["Y", "N"] = Field(default="N", alias="kycStatus")
    account_type: Optional[str] = Field(None, max_length=50, alias="accountType")
    holding_type: Optional[str] = Field(None, max_length=50, alias="holdingType")
    tax_status: Optional[str] = Field(None, max_length=50, alias="taxStatus")

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    # Pydantic V2 model_config for ORM mode and alias handling
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = Field(None, alias="createdByUserId")

# --- Scheme Schemas --- #
class SchemeBase(BaseModel):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    scheme_code: str = Field(..., max_length=50, alias="schemeCode")
    scheme_name: str = Field(..., max_length=255, alias="schemeName")
    amc_code: Optional[str] = Field(None, max_length=50, alias="amcCode")
    rta_code: Optional[str] = Field(None, max_length=50, alias="rtaCode")
    isin: Optional[str] = Field(None, max_length=12)
    category: Optional[str] = Field(None, max_length=100)
    is_active: bool = Field(default=True, alias="isActive")

class SchemeCreate(SchemeBase):
    pass

class Scheme(SchemeBase):
    # Pydantic V2 model_config for ORM mode and alias handling
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    added_at: datetime

# --- Base Order Models --- #
class OrderBase(BaseModel):
    """Base model for all order types with common fields"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field(..., max_length=3)
    unique_ref_no: str = Field(..., max_length=19, description="Unique reference number from member")
    order_id: Optional[str] = Field(None, max_length=8)
    user_id: str = Field(..., max_length=5)
    member_id: str = Field(..., max_length=20)
    client_code: str = Field(..., max_length=20)
    scheme_code: str = Field(..., max_length=20)
    dp_txn_mode: DPTxnMode = Field(DPTxnMode.PHYSICAL)
    folio_no: Optional[str] = Field(None, max_length=20)
    remarks: Optional[str] = Field(None, max_length=255)
    kyc_status: str = Field("Y", max_length=1)
    sub_broker_arn: Optional[str] = Field(None, max_length=15)
    euin: Optional[str] = Field(None, max_length=20)
    euin_declaration: bool = Field(False)
    min_redeem: bool = Field(False)
    ip_address: Optional[str] = Field(None, max_length=20)

# --- Lumpsum Order Models --- #
class LumpsumOrderCreate(OrderBase):
    """Lumpsum order creation model matching BSE specs"""
    transaction_type: TransactionType
    buy_sell_type: BuySellType = Field(BuySellType.FRESH)
    amount: Optional[decimal.Decimal] = Field(None, max_digits=14, decimal_places=2)
    quantity: Optional[decimal.Decimal] = Field(None, max_digits=8, decimal_places=3)
    all_units_flag: bool = Field(False)
    dpc_flag: bool = Field(False)

    @field_validator('amount', 'quantity')
    def validate_amount_or_quantity(cls, v, values):
        if 'amount' not in values and 'quantity' not in values:
            raise ValueError("Either amount or quantity must be provided")
        return v

class LumpsumOrderResponse(BaseModel):
    message: str
    order_id: str
    unique_ref_no: str
    bse_order_id: str
    status: str
    bse_status_code: str
    bse_remarks: Optional[str]

# --- SIP Order Models --- #
class SIPOrderCreate(OrderBase):
    """SIP order creation model matching BSE specs"""
    frequency_type: SIPFrequency
    frequency_allowed: int = Field(1, ge=1, le=99)
    installment_amount: decimal.Decimal = Field(..., max_digits=14, decimal_places=2)
    no_of_installments: int = Field(..., ge=1, le=9999)
    start_date: date = Field(...)
    first_order_today: bool = Field(False)
    mandate_id: str = Field(..., max_length=20)
    brokerage: Optional[decimal.Decimal] = Field(None, max_digits=8, decimal_places=2)
    internal_ref_no: Optional[str] = Field(None, max_length=25)

class SIPOrderModify(BaseModel):
    """SIP order modification model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field("MODSIP", max_length=3)
    unique_ref_no: str = Field(..., max_length=19)
    sip_reg_id: str = Field(..., max_length=10)
    member_id: str = Field(..., max_length=20)
    client_code: str = Field(..., max_length=20)
    user_id: str = Field(..., max_length=5)
    new_amount: Optional[decimal.Decimal] = Field(None, max_digits=14, decimal_places=2)
    new_installments: Optional[int] = Field(None, ge=1, le=9999)

class SIPOrderResponse(BaseModel):
    message: str
    sip_id: Optional[str]
    unique_ref_no: Optional[str]
    bse_sip_reg_id: Optional[str]
    status: str
    bse_status_code: Optional[str]
    bse_remarks: Optional[str]

# --- Switch Order Models --- #
class SwitchOrderCreate(OrderBase):
    """Switch order creation model matching BSE specs"""
    from_scheme_code: str = Field(..., max_length=20)
    to_scheme_code: str = Field(..., max_length=20)
    buy_sell_type: BuySellType = Field(BuySellType.FRESH)
    switch_amount: Optional[decimal.Decimal] = Field(None, max_digits=14, decimal_places=2)
    switch_units: Optional[decimal.Decimal] = Field(None, max_digits=8, decimal_places=3)
    all_units_flag: bool = Field(False)

    @field_validator('switch_amount', 'switch_units')
    def validate_amount_or_units(cls, v, values):
        if 'switch_amount' not in values and 'switch_units' not in values:
            raise ValueError("Either amount or units must be provided")
        return v

class SwitchOrderResponse(BaseModel):
    message: str
    order_id: str
    unique_ref_no: str
    bse_order_id: str
    status: str
    bse_status_code: str
    bse_remarks: Optional[str]

# --- Spread Order Models --- #
class SpreadOrderCreate(OrderBase):
    """Spread order creation model matching BSE specs"""
    buy_sell: str = Field(..., max_length=1)
    buy_sell_type: BuySellType = Field(BuySellType.FRESH)
    purchase_amount: Optional[decimal.Decimal] = Field(None, max_digits=14, decimal_places=2)
    redemption_amount: Optional[decimal.Decimal] = Field(None, max_digits=14, decimal_places=2)
    all_units_flag: bool = Field(False)
    redeem_date: date = Field(...)

class SpreadOrderResponse(BaseModel):
    message: str
    order_id: str
    unique_ref_no: str
    bse_order_id: str
    status: str
    bse_status_code: str
    bse_remarks: Optional[str]

# --- Order Status Models --- #
class OrderStatusQuery(BaseModel):
    clientCode: str
    fromDate: date
    toDate: date
    orderId: Optional[str] = None
    status: Optional[str] = None

class OrderStatusHistoryResponse(BaseModel):
    status: str
    remarks: Optional[str]
    createdAt: datetime
    createdBy: str

class OrderDetailResponse(BaseModel):
    internalOrderId: int
    orderId: Optional[str]
    uniqueRefNo: str
    orderDate: date
    orderTime: str
    clientCode: str
    clientName: Optional[str]
    schemeCode: str
    schemeName: Optional[str]
    orderType: str
    transactionType: str
    amount: Optional[decimal.Decimal]
    quantity: Optional[decimal.Decimal]
    folioNo: Optional[str]
    orderStatus: str
    paymentStatus: Optional[str]
    paymentReference: Optional[str]
    paymentDate: Optional[datetime]
    allotmentDate: Optional[datetime]
    allotmentNav: Optional[decimal.Decimal]
    unitsAllotted: Optional[decimal.Decimal]
    settlementDate: Optional[datetime]
    settlementAmount: Optional[decimal.Decimal]
    statusHistory: List[OrderStatusHistoryResponse]
    remarks: Optional[str]

class EnhancedOrderStatusResponse(BaseModel):
    status: str
    data: List[OrderDetailResponse]

# --- Order Cancellation Models --- #
class OrderCancellationResponse(BaseModel):
    message: str
    order_id: str
    status: str
    bse_status_code: str
    bse_remarks: Optional[str]

# --- General API Responses --- #
class GenericResponse(BaseModel):
    status: str
    message: str

class NAVRequest(BaseModel):
    """Schema for NAV price discovery request."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    scheme_code: str = Field(..., description="BSE Scheme Code")
    date: Optional[date] = Field(None, description="Date for NAV (defaults to current date)")
    user_id: Optional[str] = None

class NAVResponse(BaseModel):
    """Schema for NAV price discovery response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    scheme_code: str = Field(..., alias="schemeCode")
    scheme_name: str = Field(..., alias="schemeName")
    nav: float
    nav_date: date = Field(..., alias="navDate")
    status: str
    status_code: str = Field(..., alias="statusCode")
    message: Optional[str] = None

class PaymentRequest(BaseModel):
    """Schema for payment initiation request."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    order_id: int = Field(..., alias="orderId")
    order_reference: str = Field(..., alias="orderReference")
    client_code: str = Field(..., alias="clientCode")
    scheme_code: str = Field(..., alias="schemeCode")
    amount: decimal.Decimal
    currency: str = "INR"
    payment_mode: Optional[str] = Field(None, alias="paymentMode")
    redirect_url: Optional[str] = Field(None, alias="redirectUrl")

class PaymentResponse(BaseModel):
    """Schema for payment initiation response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    payment_reference: str = Field(..., alias="paymentReference")
    payment_url: str = Field(..., alias="paymentUrl")
    amount: decimal.Decimal
    currency: str
    status: str
    gateway_response: Dict[str, Any] = Field(..., alias="gatewayResponse")

class PaymentVerificationResponse(BaseModel):
    """Schema for payment verification response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    verified: bool
    status: str
    amount: Optional[decimal.Decimal] = None
    payment_id: Optional[str] = Field(None, alias="paymentId")
    payment_method: Optional[str] = Field(None, alias="paymentMethod")
    payment_time: Optional[datetime] = Field(None, alias="paymentTime")
    message: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = Field(None, alias="gatewayResponse")

class OrderResponse(BaseModel):
    """Standard response format for all order types"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field(..., max_length=3)
    unique_ref_no: str = Field(..., max_length=19)
    order_id: Optional[str] = Field(None, max_length=8)
    user_id: str = Field(..., max_length=5)
    member_id: str = Field(..., max_length=20)
    client_code: str = Field(..., max_length=20)
    bse_remarks: Optional[str] = Field(None, max_length=1000)
    success_flag: str = Field(..., max_length=1)
    si_order_id: Optional[str] = Field(None, max_length=8)  # For switch orders
    xsip_reg_id: Optional[str] = Field(None, max_length=10)  # For XSIP orders

class OrderStatusRequest(BaseModel):
    """Order status request model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    member_code: str = Field(..., max_length=10)
    user_id: str = Field(..., max_length=20)
    password: str = Field(..., max_length=30)
    from_date: date = Field(...)
    to_date: date = Field(...)
    client_code: Optional[str] = Field(None, max_length=20)
    transaction_type: Optional[str] = Field(None, max_length=5)  # P/R
    order_type: Optional[str] = Field(None, max_length=10)  # ALL/MFD/SIP/XSIP/STP/SWP
    sub_order_type: Optional[str] = Field(None, max_length=10)  # ALL/NFO/SPOR/SWITCH
    settlement_type: Optional[str] = Field(None, max_length=10)  # ALL/L0/L1/OTHERS
    order_no: Optional[str] = Field(None, max_length=20)

    @field_validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v and v not in ['P', 'R']:
            raise ValueError("Transaction type must be P or R")
        return v

    @field_validator('order_type')
    def validate_order_type(cls, v):
        valid_types = ['ALL', 'MFD', 'SIP', 'XSIP', 'STP', 'SWP']
        if v and v not in valid_types:
            raise ValueError(f"Order type must be one of {valid_types}")
        return v

    @field_validator('sub_order_type')
    def validate_sub_order_type(cls, v):
        valid_types = ['ALL', 'NFO', 'SPOR', 'SWITCH']
        if v and v not in valid_types:
            raise ValueError(f"Sub order type must be one of {valid_types}")
        return v

    @field_validator('settlement_type')
    def validate_settlement_type(cls, v):
        valid_types = ['ALL', 'L0', 'L1', 'OTHERS']
        if v and v not in valid_types:
            raise ValueError(f"Settlement type must be one of {valid_types}")
        return v

class OrderStatusResponse(BaseModel):
    """Order status response model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    status_code: str = Field(..., max_length=3)
    member_code: str = Field(..., max_length=10)
    client_code: str = Field(..., max_length=20)
    order_no: str = Field(..., max_length=20)
    bse_remarks: Optional[str] = Field(None, max_length=500)
    order_status: str = Field(..., max_length=20)
    order_remarks: Optional[str] = Field(None, max_length=200)
    scheme_code: str = Field(..., max_length=20)
    scheme_name: str = Field(..., max_length=100)
    isin: str = Field(..., max_length=12)
    buy_sell: str = Field(..., max_length=1)  # P/R
    amount: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=2)
    quantity: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=3)
    allotted_nav: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=4)
    allotted_units: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=4)
    allotment_date: Optional[date] = None
    valid_flag: str = Field(..., max_length=1)  # Y/N
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    dp_txn: str = Field(..., max_length=1)  # P/D
    settlement_type: str = Field(..., max_length=2)  # L0/L1
    order_type: str = Field(..., max_length=5)  # MFD/SIP/XSIP/STP/SWP
    sub_order_type: str = Field(..., max_length=10)  # NFO/SPOR/SWITCH
    euin: Optional[str] = Field(None, max_length=20)
    euin_flag: Optional[str] = Field(None, max_length=1)  # Y/N
    sub_broker_arn: Optional[str] = Field(None, max_length=20)
    payment_status: Optional[str] = Field(None, max_length=20)
    settlement_status: Optional[str] = Field(None, max_length=20)
    sip_reg_id: Optional[str] = Field(None, max_length=20)
    sub_broker_code: Optional[str] = Field(None, max_length=20)
    kyc_flag: str = Field(..., max_length=1)  # Y/N
    min_redeem_flag: Optional[str] = Field(None, max_length=1)  # Y/N

class AllotmentStatementRequest(BaseModel):
    """Allotment statement request model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    member_code: str = Field(..., max_length=10)
    user_id: str = Field(..., max_length=20)
    password: str = Field(..., max_length=30)
    from_date: date = Field(...)
    to_date: date = Field(...)
    client_code: Optional[str] = Field(None, max_length=20)
    order_type: Optional[str] = Field(None, max_length=10)  # ALL/MFD/SIP/XSIP/STP/SWP
    sub_order_type: Optional[str] = Field(None, max_length=10)  # ALL/NFO/SPOR/SWITCH
    settlement_type: Optional[str] = Field(None, max_length=10)  # ALL/L0/L1/OTHERS
    order_no: Optional[str] = Field(None, max_length=20)

class AllotmentStatementResponse(BaseModel):
    """Allotment statement response model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    report_date: date = Field(...)
    order_no: str = Field(..., max_length=20)
    scheme_code: str = Field(..., max_length=20)
    scheme_name: str = Field(..., max_length=100)
    amount: decimal.Decimal = Field(..., max_digits=15, decimal_places=2)
    nav: decimal.Decimal = Field(..., max_digits=15, decimal_places=4)
    units_allotted: decimal.Decimal = Field(..., max_digits=15, decimal_places=4)
    valid_flag: str = Field(..., max_length=1)  # Y/N
    remarks: Optional[str] = Field(None, max_length=200)
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    client_code: str = Field(..., max_length=20)
    client_name: str = Field(..., max_length=100)
    sip_reg_id: Optional[str] = Field(None, max_length=20)
    order_type: str = Field(..., max_length=20)

class RedemptionStatementRequest(BaseModel):
    """Redemption statement request model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    member_code: str = Field(..., max_length=10)
    user_id: str = Field(..., max_length=20)
    password: str = Field(..., max_length=30)
    from_date: date = Field(...)
    to_date: date = Field(...)
    client_code: Optional[str] = Field(None, max_length=20)
    order_type: Optional[str] = Field(None, max_length=10)  # ALL/MFD/SIP/XSIP/STP/SWP
    sub_order_type: Optional[str] = Field(None, max_length=10)  # ALL/NFO/SPOR/SWITCH
    settlement_type: Optional[str] = Field(None, max_length=10)  # ALL/L0/L1/OTHERS
    order_no: Optional[str] = Field(None, max_length=20)

class RedemptionStatementResponse(BaseModel):
    """Redemption statement response model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    report_date: date = Field(...)
    order_no: str = Field(..., max_length=20)
    scheme_code: str = Field(..., max_length=20)
    scheme_name: str = Field(..., max_length=100)
    amount: decimal.Decimal = Field(..., max_digits=15, decimal_places=2)
    nav: decimal.Decimal = Field(..., max_digits=15, decimal_places=4)
    units_redeemed: decimal.Decimal = Field(..., max_digits=15, decimal_places=4)
    valid_flag: str = Field(..., max_length=1)  # Y/N
    remarks: Optional[str] = Field(None, max_length=200)
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    client_code: str = Field(..., max_length=20)
    client_name: str = Field(..., max_length=100)
    settlement_type: str = Field(..., max_length=2)  # L0/L1
    order_type: str = Field(..., max_length=20)

