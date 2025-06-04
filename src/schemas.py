# /home/ubuntu/order_management_system/src/schemas.py

from pydantic import BaseModel, Field, EmailStr, validator, field_validator, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
import decimal

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

# --- Order Schemas --- #
class OrderBase(BaseModel):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    unique_ref_no: str = Field(..., max_length=50, alias="uniqueRefNo")
    client_code: str = Field(..., max_length=50, alias="clientCode")
    scheme_code: str = Field(..., max_length=50, alias="schemeCode")
    folio_no: Optional[str] = Field(None, max_length=50, alias="folioNo")
    ip_address: Optional[str] = Field(None, max_length=45, alias="ipAddress")
    euin: Optional[str] = Field(None, max_length=50)
    euin_declared: Optional[Literal["Y", "N"]] = Field(None, alias="euinDeclared")
    sub_arn_code: Optional[str] = Field(None, max_length=50, alias="subArnCode")

class LumpsumOrderCreate(OrderBase):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    transactionType: Literal["PURCHASE", "REDEMPTION"] = Field(..., alias="transactionType")
    amount: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=2)
    quantity: Optional[decimal.Decimal] = Field(None, max_digits=15, decimal_places=4)
    dpTxnMode: Optional[str] = Field(None, alias="dpTxnMode")
    kycStatus: Literal["Y", "N"] = Field(..., alias="kycStatus")
    remarks: Optional[str] = None

    # # Pydantic V2 validator syntax - Temporarily commented out to isolate alias parsing issue
    # @field_validator("amount", "quantity", mode="before")
    # @classmethod
    # def check_amount_or_quantity(cls, v, info):
    #     values = info.data # Access the raw input data (should contain aliases)
    #     ttype = values.get("transactionType")
    #     # Check both alias and field name for amount
    #     amount_val = values.get("amount", v) 
    #     if ttype == "PURCHASE" and amount_val is None:
    #         raise ValueError("Amount is required for PURCHASE")
    #     if ttype == "REDEMPTION" and amount_val is not None:
    #         pass # Allow amount for redemption if API supports it
    #     # Add quantity validation for redemption if needed
    #     return v

class LumpsumOrderResponse(BaseModel):
    # Pydantic V2 model_config for alias handling (output)
    model_config = ConfigDict(populate_by_name=True)

    statusCode: str = Field(..., alias="statusCode")
    message: str
    clientCode: str = Field(..., alias="clientCode")
    orderId: Optional[str] = Field(None, alias="orderId")
    uniqueRefNo: str = Field(..., alias="uniqueRefNo")
    bseRemarks: Optional[str] = Field(None, alias="bseRemarks")
    successFlag: Literal["Y", "N"] = Field(..., alias="successFlag")

class SIPOrderCreate(OrderBase):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    amount: decimal.Decimal = Field(..., max_digits=15, decimal_places=2)
    frequency: str
    startDate: date = Field(..., alias="startDate")
    endDate: Optional[date] = Field(None, alias="endDate")
    installments: Optional[int] = None
    firstOrderToday: Literal["Y", "N"] = Field(..., alias="firstOrderToday")
    mandateId: Optional[str] = Field(None, alias="mandateId")
    brokerage: Optional[str] = None
    remarks: Optional[str] = None

    # Pydantic V2 validator syntax
    @field_validator("endDate", "installments", mode="before")
    @classmethod
    def check_end_date_or_installments(cls, v, info):
        values = info.data
        if values.get("endDate") is None and values.get("installments") is None:
            raise ValueError("Either endDate or installments must be provided for SIP")
        if values.get("endDate") is not None and values.get("installments") is not None:
            raise ValueError("Provide either endDate or installments for SIP, not both")
        return v

class SIPOrderResponse(BaseModel):
    # Pydantic V2 model_config for alias handling (output)
    model_config = ConfigDict(populate_by_name=True)

    statusCode: str = Field(..., alias="statusCode")
    message: str
    clientCode: str = Field(..., alias="clientCode")
    sipRegId: Optional[str] = Field(None, alias="sipRegId")
    uniqueRefNo: str = Field(..., alias="uniqueRefNo")
    bseRemarks: Optional[str] = Field(None, alias="bseRemarks")
    successFlag: Literal["Y", "N"] = Field(..., alias="successFlag")

class OrderStatusQuery(BaseModel):
    # Pydantic V2 model_config for alias handling (input from query params)
    model_config = ConfigDict(populate_by_name=True)

    clientCode: str = Field(..., alias="clientCode")
    fromDate: date = Field(..., alias="fromDate")
    toDate: date = Field(..., alias="toDate")
    orderId: Optional[str] = Field(None, alias="orderId")
    status: Optional[str] = None
    memberId: str = Field(..., alias="memberId")

class OrderStatusDetail(BaseModel):
    # Pydantic V2 model_config for ORM mode and alias handling (output)
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    orderId: Optional[str] = Field(None, alias="orderId")
    internalOrderId: int = Field(..., alias="internalOrderId")
    uniqueRefNo: str = Field(..., alias="uniqueRefNo")
    orderDate: date = Field(..., alias="orderDate")
    orderTime: Optional[str] = Field(None, alias="orderTime")
    clientCode: str = Field(..., alias="clientCode")
    clientName: Optional[str] = Field(None, alias="clientName")
    schemeCode: str = Field(..., alias="schemeCode")
    schemeName: Optional[str] = Field(None, alias="schemeName")
    orderType: str = Field(..., alias="orderType")
    transactionType: Optional[str] = Field(None, alias="transactionType")
    amount: Optional[decimal.Decimal] = None
    quantity: Optional[decimal.Decimal] = None
    price: Optional[decimal.Decimal] = None
    folioNo: Optional[str] = Field(None, alias="folioNo")
    orderStatus: str = Field(..., alias="orderStatus")
    allotmentDate: Optional[date] = Field(None, alias="allotmentDate")
    remarks: Optional[str] = None

class OrderStatusResponse(BaseModel):
    # Pydantic V2 model_config for alias handling (output)
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["Success", "Failed"]
    data: Optional[List[OrderStatusDetail]] = None
    message: Optional[str] = None

# --- Mandate Schemas (Placeholder) --- #
class MandateBase(BaseModel):
    # Pydantic V2 model_config for alias handling
    model_config = ConfigDict(populate_by_name=True)

    mandate_id: str = Field(..., max_length=50, alias="mandateId")
    client_code: str = Field(..., max_length=50, alias="clientCode")
    bank_account_no: str = Field(..., max_length=50, alias="bankAccountNo")
    bank_name: str = Field(..., max_length=100, alias="bankName")
    ifsc_code: str = Field(..., max_length=11, alias="ifscCode")
    amount: decimal.Decimal = Field(..., max_digits=15, decimal_places=2)
    mandate_type: str = Field(..., max_length=20, alias="mandateType")
    status: str = Field(default="PENDING", max_length=30)
    registration_date: Optional[date] = Field(None, alias="registrationDate")
    expiry_date: Optional[date] = Field(None, alias="expiryDate")

class MandateCreate(MandateBase):
    pass

class Mandate(MandateBase):
    # Pydantic V2 model_config for ORM mode and alias handling
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    created_at: datetime
    updated_at: Optional[datetime] = None

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

class OrderStatusHistoryResponse(BaseModel):
    """Schema for order status history entry."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    status: str
    remarks: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    created_by: str = Field(..., alias="createdBy")

class EnhancedOrderStatusDetail(OrderStatusDetail):
    """Enhanced order status detail with additional tracking information."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    paymentStatus: Optional[str] = Field(None, alias="paymentStatus")
    paymentReference: Optional[str] = Field(None, alias="paymentReference")
    paymentDate: Optional[datetime] = Field(None, alias="paymentDate")
    allotmentDate: Optional[datetime] = Field(None, alias="allotmentDate")
    allotmentNav: Optional[decimal.Decimal] = Field(None, alias="allotmentNav")
    unitsAllotted: Optional[decimal.Decimal] = Field(None, alias="unitsAllotted")
    settlementDate: Optional[datetime] = Field(None, alias="settlementDate")
    settlementAmount: Optional[decimal.Decimal] = Field(None, alias="settlementAmount")
    statusHistory: List[OrderStatusHistoryResponse] = Field(default_factory=list, alias="statusHistory")

class EnhancedOrderStatusResponse(BaseModel):
    """Enhanced response model for order status endpoint."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    status: str
    data: List[EnhancedOrderStatusDetail]

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

