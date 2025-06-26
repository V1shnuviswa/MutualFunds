# /home/ubuntu/order_management_system/src/schemas.py

from pydantic import BaseModel, Field, EmailStr, validator, field_validator, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
from decimal import Decimal
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
    model_config = ConfigDict(populate_by_name=True)

    userId: str = Field(..., alias="userId")
    memberId: str = Field(..., alias="memberId")
    password: str
    passKey: Optional[str] = Field(None, alias="passKey")

class UserInDBBase(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class User(UserInDBBase):
    pass

# --- Client Schemas --- #
class ClientBase(BaseModel):
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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_user_id: Optional[int] = Field(None, alias="createdByUserId")

# --- Scheme Schemas --- #
class SchemeBase(BaseModel):
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
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    added_at: datetime

# --- Base Order Models --- #
class OrderBase(BaseModel):
    """Base model for all order types with common fields"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field(..., max_length=3)
    unique_ref_no: str = Field(..., max_length=19, description="Unique reference number from member")
    order_id: Optional[str] = Field(None, max_length=8)
    user_id: str = Field(..., max_length=20)
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
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class LumpsumOrderRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    TransCode: str = Field("NEW", description="Order: NEW/Modification/Cancellation")
    TransNo: str = Field(..., description="Unique reference number")
    RefNo: str = Field(..., description="Unique reference number for BSE")
    UserID: str = Field(..., description="BSE User ID")
    MemberId: str = Field(..., description="BSE Member ID")
    ClientCode: str = Field(..., description="Client code")
    SchemeCd: str = Field(..., description="BSE scheme code")
    BuySell: str = Field(..., description="Type of transaction (P/R)")
    BuySellType: str = Field("FRESH", description="FRESH/ADDITIONAL")
    DPTxn: str = Field(..., description="CDSL/NSDL/PHYSICAL")
    Amount: float = Field(None, description="Amount for purchase/redemption")
    Qty: float = Field(None, description="Quantity for redemption")
    AllRedeem: str = Field("N", description="All units flag (Y/N)")
    FolioNo: Optional[str] = Field(..., description="Folio number")
    Remarks: Optional[str] = Field(None, description="Additional comments")
    KYCStatus: str = Field("Y", description="KYC status (Y/N)")
    SubBrokerARN: Optional[str] = Field(None, description="Sub broker code")
    EUIN: str = Field(..., description="EUIN code")
    EUINFlag: str = Field("N", description="EUIN declaration (Y/N)")
    MinRedeem: str = Field("N", description="Minimum redemption flag (Y/N)")
    DPC: str = Field("Y", description="DPC flag (Y)")
    IPAdd: Optional[str] = Field(None, description="Client IP address")
    Password: str = Field(..., description="Encrypted password")
    PassKey: str = Field(..., description="Pass Key")
    MobileNo: Optional[str] = Field(None, description="Mobile number")
    EmailID: Optional[str] = Field(None, description="Email ID")
    MandateID: Optional[str] = Field(None, description="Mandate ID")



    
   

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
    installment_amount: Decimal = Field(..., max_digits=14, decimal_places=2)
    no_of_installments: int = Field(..., ge=1, le=9999)
    start_date: date = Field(...)
    first_order_today: bool = Field(False)
    mandate_id: str = Field(..., max_length=20)
    brokerage: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    dpc_flag: bool = Field(False)

class SIPOrderModify(BaseModel):
    """SIP order modification model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field("MODSIP", max_length=3)
    unique_ref_no: str = Field(..., max_length=19)
    sip_reg_id: str = Field(..., max_length=10)
    member_id: str = Field(..., max_length=20)
    client_code: str = Field(..., max_length=20)
    user_id: str = Field(..., max_length=20)
    new_amount: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    new_installments: Optional[int] = Field(None, ge=1, le=9999)

class SIPOrderResponse(BaseModel):
    message: str
    sip_id: Optional[str]
    unique_ref_no: Optional[str]
    bse_sip_reg_id: Optional[str]
    status: str
    bse_status_code: Optional[str]
    bse_remarks: Optional[str]

# --- XSIP Order Models --- #
class XSIPOrderCreate(OrderBase):
    """XSIP order creation model matching BSE specs"""
    frequency_type: SIPFrequency
    frequency_allowed: int = Field(1, ge=1, le=99)
    installment_amount: Decimal = Field(..., max_digits=14, decimal_places=2)
    no_of_installments: int = Field(..., ge=1, le=9999)
    start_date: date = Field(...)
    first_order_today: bool = Field(False)
    mandate_id: str = Field(..., max_length=20)
    brokerage: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    dpc_flag: bool = Field(False)
    xsip_reg_id: Optional[str] = Field(None, max_length=20)

class XSIPOrderModify(BaseModel):
    """XSIP order modification model matching BSE specs"""
    model_config = ConfigDict(populate_by_name=True)

    transaction_code: str = Field("MODXSIP", max_length=3)
    unique_ref_no: str = Field(..., max_length=19)
    xsip_reg_id: str = Field(..., max_length=10)
    member_id: str = Field(..., max_length=20)
    client_code: str = Field(..., max_length=20)
    user_id: str = Field(..., max_length=20)
    new_amount: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    new_installments: Optional[int] = Field(None, ge=1, le=9999)

class XSIPOrderResponse(BaseModel):
    message: str
    xsip_id: Optional[str]
    unique_ref_no: Optional[str]
    bse_xsip_reg_id: Optional[str]
    status: str
    bse_status_code: Optional[str]
    bse_remarks: Optional[str]

# --- Switch Order Models --- #
class SwitchOrderCreate(OrderBase):
    """Switch order creation model matching BSE specs"""
    from_scheme_code: str = Field(..., max_length=20)
    to_scheme_code: str = Field(..., max_length=20)
    buy_sell_type: BuySellType = Field(BuySellType.FRESH)
    switch_amount: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    switch_units: Optional[Decimal] = Field(None, max_digits=8, decimal_places=3)
    all_units_flag: bool = Field(False)

    @field_validator('switch_amount', 'switch_units')
    @classmethod
    def validate_amount_or_units(cls, v, info):
        if 'switch_amount' not in info.data and 'switch_units' not in info.data:
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
    purchase_amount: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    redemption_amount: Optional[Decimal] = Field(None, max_digits=14, decimal_places=2)
    all_units_flag: bool = Field(False)
    redeem_date: date = Field(...)

class SpreadOrderResponse(BaseModel):
    message: str
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

class OrderStatusResponse(BaseModel):
    """Base response model for order status endpoints"""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Response status (Success/Failed)")
    message: Optional[str] = Field(None, description="Additional message if any")
    order_id: Optional[str] = Field(None, description="Order ID if available") 

class OrderStatusHistoryResponse(BaseModel):
    """Response model for order status history"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="Order status")
    remarks: Optional[str] = Field(None, description="Status change remarks")
    createdAt: datetime = Field(..., description="When status was created")
    createdBy: str = Field(..., description="User who created the status")

class EnhancedOrderStatusDetail(BaseModel):
    """Detailed order status model including tracking information"""
    model_config = ConfigDict(from_attributes=True)
    
    internalOrderId: int = Field(..., description="Internal order ID")
    orderId: Optional[str] = Field(None, description="BSE order ID")
    uniqueRefNo: str = Field(..., description="Unique reference number")
    orderDate: date = Field(..., description="Date order was placed")
    orderTime: str = Field(..., description="Time order was placed")
    clientCode: str = Field(..., description="Client code")
    clientName: Optional[str] = Field(None, description="Client name")
    schemeCode: str = Field(..., description="Scheme code")
    schemeName: Optional[str] = Field(None, description="Scheme name")
    orderType: str = Field(..., description="Type of order")
    transactionType: str = Field(..., description="Type of transaction")
    amount: Optional[Decimal] = Field(None, description="Order amount")
    quantity: Optional[Decimal] = Field(None, description="Order quantity")
    folioNo: Optional[str] = Field(None, description="Folio number")
    orderStatus: str = Field(..., description="Current order status")
    paymentStatus: Optional[str] = Field(None, description="Payment status")
    paymentReference: Optional[str] = Field(None, description="Payment reference")
    paymentDate: Optional[datetime] = Field(None, description="Payment date")
    allotmentDate: Optional[datetime] = Field(None, description="Allotment date")
    allotmentNav: Optional[Decimal] = Field(None, description="Allotment NAV")
    unitsAllotted: Optional[Decimal] = Field(None, description="Units allotted")
    settlementDate: Optional[datetime] = Field(None, description="Settlement date")
    settlementAmount: Optional[Decimal] = Field(None, description="Settlement amount")
    remarks: Optional[str] = Field(None, description="Order remarks")
    statusHistory: List[OrderStatusHistoryResponse] = Field(..., description="Status change history")

class EnhancedOrderStatusResponse(BaseModel):
    """Response model for enhanced order status endpoints"""
    model_config = ConfigDict(from_attributes=True)
    
    status: str = Field(..., description="Response status")
    data: List[EnhancedOrderStatusDetail] = Field(..., description="Order status details")

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
    nav_date: Optional[date] = None
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
    amount: Decimal
    currency: str = "INR"
    payment_mode: Optional[str] = Field(None, alias="paymentMode")
    redirect_url: Optional[str] = Field(None, alias="redirectUrl")

class PaymentResponse(BaseModel):
    """Schema for payment initiation response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    payment_reference: str = Field(..., alias="paymentReference")
    payment_url: str = Field(..., alias="paymentUrl")
    amount: Decimal
    currency: str
    status: str
    gateway_response: Dict[str, Any] = Field(..., alias="gatewayResponse")

class PaymentVerificationResponse(BaseModel):
    """Schema for payment verification response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    verified: bool
    status: str
    amount: Optional[Decimal] = None
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
    user_id: str = Field(..., max_length=20)
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
    amount: Decimal = Field(..., max_digits=15, decimal_places=2)
    nav: Decimal = Field(..., max_digits=15, decimal_places=4)
    units_allotted: Decimal = Field(..., max_digits=15, decimal_places=4)
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
    amount: Decimal = Field(..., max_digits=15, decimal_places=2)
    nav: Decimal = Field(..., max_digits=15, decimal_places=4)
    units_redeemed: Decimal = Field(..., max_digits=15, decimal_places=4)
    valid_flag: str = Field(..., max_length=1)  # Y/N
    remarks: Optional[str] = Field(None, max_length=200)
    internal_ref_no: Optional[str] = Field(None, max_length=25)
    client_code: str = Field(..., max_length=20)
    client_name: str = Field(..., max_length=100)
    settlement_type: str = Field(..., max_length=2)  # L0/L1
    order_type: str = Field(..., max_length=20)

# --- Holdings Schemas --- #
class HoldingResponse(BaseModel):
    """Schema for holdings response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    clientCode: str
    folioNo: str
    schemeCode: str
    schemeName: str
    isin: str
    units: float
    navValue: float
    currentValue: float
    purchaseValue: float
    purchaseDate: str
    gainLoss: float
    gainLossPercentage: float

# --- Instrument Schemas --- #
class InstrumentResponse(BaseModel):
    """Schema for instruments response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    schemeCode: str
    schemeName: str
    amcCode: Optional[str] = None
    rtaCode: Optional[str] = None
    isin: Optional[str] = None
    category: Optional[str] = None
    isActive: bool = True
    minInvestment: float
    sipMinimum: float
    purchaseAllowed: bool = True
    redemptionAllowed: bool = True
    sipAllowed: bool = True
    switchAllowed: bool = True

class InstrumentDetailResponse(InstrumentResponse):
    """Schema for detailed instrument response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    amcName: Optional[str] = None
    rtaName: Optional[str] = None
    subCategory: Optional[str] = None
    exitLoad: Optional[str] = None
    expenseRatio: Optional[float] = None
    fundManager: Optional[str] = None
    launchDate: Optional[str] = None
    fundSize: Optional[float] = None
    nav: Optional[float] = None
    navDate: Optional[str] = None
    riskCategory: Optional[str] = None
    benchmark: Optional[str] = None
    settlementDays: Optional[int] = None

# --- SIP Detail Schema --- #
class SIPDetailResponse(BaseModel):
    """Schema for SIP details response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    sipId: str
    bseSipRegId: Optional[str] = None
    clientCode: str
    clientName: Optional[str] = None
    schemeCode: str
    schemeName: Optional[str] = None
    frequency: str
    amount: Decimal
    installments: Optional[int] = None
    startDate: date
    endDate: Optional[date] = None
    mandateId: Optional[str] = None
    firstOrderToday: bool = False
    status: str
    createdAt: datetime
    updatedAt: Optional[datetime] = None
    orderId: Optional[str] = None
    orderStatus: Optional[str] = None

# --- Client Registration Schemas --- #

class RegistrationStep1(BaseModel):
    """Step 1: Personal details & investment mode"""
    model_config = ConfigDict(populate_by_name=True)
    
    client_name: str = Field(..., max_length=255)
    email: EmailStr
    mobile: str = Field(..., pattern=r'^\d{10}$')
    investment_mode: str = Field(..., description="Individual, Joint, etc.")

class RegistrationStep2(BaseModel):
    """Step 2: Investment type preferences"""
    model_config = ConfigDict(populate_by_name=True)
    
    investment_type: str = Field(..., description="LUMPSUM, SIP, etc.")
    risk_profile: Optional[str] = None
    investment_horizon: Optional[str] = None

class RegistrationStep3(BaseModel):
    """Step 3: Scheme selection"""
    model_config = ConfigDict(populate_by_name=True)
    
    scheme_code: str
    plan_type: str = Field(..., description="Direct Plan, Regular Plan, etc.")

class RegistrationStep4(BaseModel):
    """Step 4: Detailed personal information"""
    model_config = ConfigDict(populate_by_name=True)
    
    tax_status: str = Field(..., description="Resident Individual, NRI, etc.")
    pan: str = Field(..., pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', description="PAN number")
    date_of_birth: date
    gender: str
    occupation: str
    annual_income: str
    pep_declaration: bool = Field(..., description="Politically Exposed Person declaration")

class RegistrationStep5(BaseModel):
    """Step 5: Address details"""
    model_config = ConfigDict(populate_by_name=True)
    
    address_type: str
    flat_door_block: str
    road_street: str
    area_locality: str
    city: str
    state: str
    country: str
    pin_code: str = Field(..., pattern=r'^\d{6}$')

class RegistrationStep6(BaseModel):
    """Step 6: Tax residency declaration"""
    model_config = ConfigDict(populate_by_name=True)
    
    is_tax_resident_of_other_country: bool
    fatca_countries: Optional[List[str]] = None
    tax_identification_numbers: Optional[List[str]] = None

class RegistrationStep7(BaseModel):
    """Step 7: Investment & bank details"""
    model_config = ConfigDict(populate_by_name=True)
    
    investment_amount: Decimal = Field(..., ge=1000)
    bank_name: str
    account_number: str
    confirm_account_number: str
    ifsc_code: str
    bank_city: str
    branch_name: str
    account_type: str

class RegistrationStep8(BaseModel):
    """Step 8: Nominee details"""
    model_config = ConfigDict(populate_by_name=True)
    
    nominee_opt_out: bool = False
    nominee_name: Optional[str] = None
    nominee_relation: Optional[str] = None
    nominee_dob: Optional[date] = None
    nominee_address: Optional[str] = None
    nominee_percentage: Optional[int] = Field(None, ge=1, le=100)

class RegistrationStateResponse(BaseModel):
    """Response with current registration state"""
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[str] = Field(None, description="New order status")
    status_code: Optional[str] = Field(None, description="BSE status code")
    remarks: Optional[str] = Field(None, description="Additional remarks or reason for status change")
    payment_status: Optional[str] = Field(None, description="Payment status")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    payment_date: Optional[datetime] = Field(None, description="Date when payment was processed")
    allotment_date: Optional[datetime] = Field(None, description="Date of unit allotment")
    allotment_nav: Optional[Decimal] = Field(None, description="NAV at which units were allotted", decimal_places=4)
    units_allotted: Optional[Decimal] = Field(None, description="Number of units allotted", decimal_places=4)
    settlement_date: Optional[datetime] = Field(None, description="Settlement date")
    settlement_amount: Optional[Decimal] = Field(None, description="Settlement amount", decimal_places=2)
    order_id_bse: Optional[str] = Field(None, description="BSE order ID")

    @field_validator('status')
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [
                "RECEIVED", "PENDING", "PAYMENT_INITIATED", "PAYMENT_COMPLETED",
                "SENT_TO_BSE", "ACCEPTED_BY_BSE", "REJECTED_BY_BSE", "CANCELLED",
                "COMPLETED", "FAILED"
            ]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v

# --- Mandate Models --- #
class MandateBase(BaseModel):
    """Base model for mandate creation and updates"""
    model_config = ConfigDict(populate_by_name=True)

    client_code: str = Field(..., max_length=20)
    mandate_type: str = Field(..., description="NACH/BILLDESK/UPI etc.")
    bank_name: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=20)
    account_type: str = Field(..., max_length=20)
    ifsc_code: str = Field(..., pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    maximum_amount: Decimal = Field(..., max_digits=14, decimal_places=2)
    start_date: date = Field(...)
    end_date: Optional[date] = None
    frequency: str = Field(..., description="MONTHLY/QUARTERLY/WEEKLY")
    approval_status: Optional[str] = Field(None, description="PENDING/APPROVED/REJECTED")

class MandateCreate(MandateBase):
    """Model for creating a new mandate"""
    pass

class MandateUpdate(BaseModel):
    """Model for updating mandate details"""
    model_config = ConfigDict(from_attributes=True)

    approval_status: Optional[str] = Field(None, description="PENDING/APPROVED/REJECTED")
    approval_reference: Optional[str] = Field(None, max_length=50)
    rejection_reason: Optional[str] = Field(None, max_length=200)
    last_status_update: Optional[datetime] = None

class MandateResponse(MandateBase):
    """Response model for mandate operations"""
    model_config = ConfigDict(from_attributes=True)
    
    mandate_id: str
    bse_mandate_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    approval_reference: Optional[str] = None
    rejection_reason: Optional[str] = None
    last_status_update: Optional[datetime] = None

class MandateStatusResponse(BaseModel):
    """Response model for mandate status check"""
    model_config = ConfigDict(from_attributes=True)

    mandate_id: str
    status: str
    message: Optional[str] = None
    bse_status_code: Optional[str] = None
    bse_remarks: Optional[str] = None

# --- Order Models --- #
class OrderUpdate(BaseModel):
    """Schema for updating an existing order"""
    model_config = ConfigDict(from_attributes=True)

    status: Optional[str] = Field(None, description="New order status")
    status_code: Optional[str] = Field(None, description="BSE status code")
    remarks: Optional[str] = Field(None, description="Additional remarks or reason for status change")
    payment_status: Optional[str] = Field(None, description="Payment status")
    payment_reference: Optional[str] = Field(None, description="Payment reference number")
    payment_date: Optional[datetime] = Field(None, description="Date when payment was processed")
    allotment_date: Optional[datetime] = Field(None, description="Date of unit allotment")
    allotment_nav: Optional[Decimal] = Field(None, description="NAV at which units were allotted")
    units_allotted: Optional[Decimal] = Field(None, description="Number of units allotted")
    settlement_date: Optional[datetime] = Field(None, description="Settlement date")
    settlement_amount: Optional[Decimal] = Field(None, description="Settlement amount")
    order_id_bse: Optional[str] = Field(None, description="BSE order ID")

    @field_validator("status")
    def validate_status(cls, v):
        if v is not None:
            valid_statuses = [
                "RECEIVED", "PENDING", "PAYMENT_INITIATED", "PAYMENT_COMPLETED",
                "SENT_TO_BSE", "ACCEPTED_BY_BSE", "REJECTED_BY_BSE", "CANCELLED",
                "COMPLETED", "FAILED"
            ]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of {valid_statuses}")
        return v

