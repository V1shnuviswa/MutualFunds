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
    SWITCH = "SWITCH"
    SPREAD = "SPREAD"

class TransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    REDEMPTION = "REDEMPTION"

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
    unique_ref_no: str = Field(..., description="Unique reference number for the order")
    client_code: str = Field(..., description="Client code")
    scheme_code: str = Field(..., description="Scheme code")
    folio_no: Optional[str] = Field(None, description="Folio number if existing")
    dp_txn_mode: str = Field("DEMAT", description="Transaction mode (DEMAT/PHYSICAL)")
    euin: Optional[str] = Field(None, description="EUIN number")
    euin_declared: bool = Field(False, description="EUIN declaration flag")
    sub_arn_code: Optional[str] = Field(None, description="Sub ARN code")
    remarks: Optional[str] = Field(None, description="Order remarks")
    ip_address: Optional[str] = Field(None, description="Client IP address")

# --- Lumpsum Order Models --- #
class LumpsumOrderCreate(OrderBase):
    transaction_type: TransactionType
    amount: Optional[decimal.Decimal] = Field(None, description="Order amount")
    quantity: Optional[decimal.Decimal] = Field(None, description="Order quantity")
    all_units_flag: bool = Field(False, description="Redeem all units flag")
    min_redeem_flag: bool = Field(False, description="Minimum redemption flag")
    dpc_flag: bool = Field(False, description="DPC flag")

    @validator('amount', 'quantity')
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
    frequency: SIPFrequency
    amount: decimal.Decimal = Field(..., description="SIP installment amount")
    installments: Optional[int] = Field(None, description="Number of installments")
    start_date: date = Field(..., description="SIP start date")
    end_date: Optional[date] = Field(None, description="SIP end date")
    mandate_id: str = Field(..., description="Mandate ID for payments")
    first_order_today: bool = Field(False, description="Place first order today")

class SIPOrderModify(BaseModel):
    sip_reg_id: str = Field(..., description="SIP registration ID")
    unique_ref_no: str = Field(..., description="Unique reference for modification")
    client_code: str = Field(..., description="Client code for validation")
    new_amount: Optional[decimal.Decimal] = Field(None, description="New SIP amount")
    new_installments: Optional[int] = Field(None, description="New number of installments")

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
    from_scheme_code: str = Field(..., description="Source scheme code")
    to_scheme_code: str = Field(..., description="Target scheme code")
    amount: Optional[decimal.Decimal] = Field(None, description="Switch amount")
    units: Optional[decimal.Decimal] = Field(None, description="Switch units")
    all_units_flag: bool = Field(False, description="Switch all units flag")

    @validator('amount', 'units')
    def validate_amount_or_units(cls, v, values):
        if 'amount' not in values and 'units' not in values:
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
    buy_sell: str = Field(..., description="Buy/Sell indicator")
    purchase_amount: Optional[decimal.Decimal] = Field(None, description="Purchase amount")
    redemption_amount: Optional[decimal.Decimal] = Field(None, description="Redemption amount")
    all_units_flag: bool = Field(False, description="All units flag")
    redeem_date: date = Field(..., description="Redemption date")

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

