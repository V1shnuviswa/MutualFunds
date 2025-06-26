# /home/ubuntu/order_management_system/src/models.py

from sqlalchemy import (
    Column, Integer, String, DateTime, DECIMAL, CHAR, TEXT, BOOLEAN, ForeignKey, Date, Numeric
)
from sqlalchemy.orm import relationship, foreign
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    member_id = Column(String(50), nullable=False)
    password_hash = Column(String(255), nullable=False)
    pass_key = Column(String(255), nullable=True) # Store securely if used
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    orders = relationship("Order", foreign_keys="[Order.user_id]", back_populates="user")
    clients_created = relationship("Client", back_populates="creator") # Optional relationship
    
    # Add PostgreSQL constraints
    __table_args__ = ()

class Client(Base):
    __tablename__ = "clients"

    client_code = Column(String(50), primary_key=True, index=True)
    client_name = Column(String(255), nullable=True)
    pan = Column(String(10), unique=True, index=True, nullable=True)
    kyc_status = Column(CHAR(1), nullable=False, default='N')
    account_type = Column(String(50), nullable=True)
    holding_type = Column(String(50), nullable=True)
    tax_status = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("User", back_populates="clients_created") # Optional relationship
    orders = relationship("Order", back_populates="client")
    sip_registrations = relationship("SIPRegistration", back_populates="client")
    mandates = relationship("Mandate", back_populates="client")
    registration_state = relationship("ClientRegistrationState", back_populates="client", uselist=False)
    
    # Add PostgreSQL constraints
    __table_args__ = ()

class Scheme(Base):
    __tablename__ = "schemes"

    scheme_code = Column(String(50), primary_key=True, index=True)
    scheme_name = Column(String(255), nullable=False)
    amc_code = Column(String(50), nullable=True)
    rta_code = Column(String(50), nullable=True)
    isin = Column(String(12), unique=True, index=True, nullable=True)
    category = Column(String(100), nullable=True)
    is_active = Column(BOOLEAN, nullable=False, default=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    orders = relationship("Order", back_populates="scheme")
    sip_registrations = relationship("SIPRegistration", back_populates="scheme")
    
    # Add PostgreSQL constraints
    __table_args__ = ()

class OrderStatusHistory(Base):
    """Model for tracking order status changes."""
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String, nullable=False)
    remarks = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    order = relationship("Order", back_populates="status_history")
    user = relationship("User", foreign_keys=[created_by])

    # Add Postgres sequence for id
    __table_args__ = ()

class Order(Base):
    """Model for orders (both lumpsum and SIP)."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id_bse = Column(String(50), unique=True, index=True, nullable=True)
    unique_ref_no = Column(String(50), unique=True, index=True, nullable=False)
    client_code = Column(String(50), ForeignKey("clients.client_code"), nullable=False, index=True)
    scheme_code = Column(String(50), ForeignKey("schemes.scheme_code"), nullable=False, index=True)
    order_type = Column(String(20), nullable=False) # e.g., LUMPSUM, SIP_REG
    transaction_type = Column(String(20), nullable=True) # e.g., PURCHASE, REDEMPTION
    amount = Column(DECIMAL(15, 2), nullable=True)
    quantity = Column(DECIMAL(15, 4), nullable=True)
    folio_no = Column(String(50), nullable=True)
    order_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, nullable=False, default="RECEIVED")
    status_code = Column(String)  # BSE status code
    status_updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status_updated_by = Column(Integer, ForeignKey("users.id"))
    payment_status = Column(String)
    payment_reference = Column(String)
    payment_date = Column(DateTime)
    allotment_date = Column(DateTime)
    allotment_nav = Column(Numeric(10, 4))
    units_allotted = Column(Numeric(10, 4))
    settlement_date = Column(DateTime)
    settlement_amount = Column(Numeric(10, 2))
    status_message = Column(TEXT, nullable=True)
    bse_status_code = Column(String(10), nullable=True)
    bse_remarks = Column(TEXT, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    euin = Column(String(50), nullable=True)
    euin_declared = Column(String(1), nullable=True, default='N')
    sub_arn_code = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    dp_txn_mode = Column(String(10), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="orders")
    client = relationship("Client", back_populates="orders")
    scheme = relationship("Scheme", back_populates="orders")
    sip_registration = relationship("SIPRegistration", back_populates="order", uselist=False) # One-to-one
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    status_updated_by_user = relationship("User", foreign_keys=[status_updated_by])

    # Add PostgreSQL sequence configuration
    __table_args__ = ()

class SIPRegistration(Base):
    __tablename__ = "sip_registrations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sip_reg_id_bse = Column(String(50), unique=True, index=True, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True) # Link to the registration order
    client_code = Column(String(50), ForeignKey("clients.client_code"), nullable=False, index=True)
    scheme_code = Column(String(50), ForeignKey("schemes.scheme_code"), nullable=False, index=True)
    frequency = Column(String(20), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    installments = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)
    mandate_id = Column(String(50), ForeignKey("mandates.mandate_id"), nullable=True, index=True)
    first_order_today = Column(CHAR(1), nullable=True)
    status = Column(String(30), nullable=False, default='REGISTERED', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    order = relationship("Order", back_populates="sip_registration")
    client = relationship("Client", back_populates="sip_registrations")
    scheme = relationship("Scheme", back_populates="sip_registrations")
    mandate = relationship("Mandate", back_populates="sip_registrations")

    # Add PostgreSQL sequence configuration
    __table_args__ = ()

class Mandate(Base):
    __tablename__ = "mandates"

    mandate_id = Column(String(50), primary_key=True, index=True)
    client_code = Column(String(50), ForeignKey("clients.client_code"), nullable=False, index=True)
    bank_account_no = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    ifsc_code = Column(String(11), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    mandate_type = Column(String(20), nullable=False)
    status = Column(String(30), nullable=False, default='PENDING', index=True)
    registration_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    client = relationship("Client", back_populates="mandates")
    sip_registrations = relationship("SIPRegistration", back_populates="mandate")
    
    # Add PostgreSQL constraints
    __table_args__ = ()

class ClientRegistrationState(Base):
    """Model for tracking client registration progress through multiple steps."""
    __tablename__ = "client_registration_states"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    client_code = Column(String(50), ForeignKey("clients.client_code"), unique=True, index=True, nullable=False)
    
    # Progress tracking
    current_step = Column(Integer, default=1)
    is_complete = Column(BOOLEAN, default=False)
    
    # Step completion status
    step1_complete = Column(BOOLEAN, default=False)  # Personal details
    step2_complete = Column(BOOLEAN, default=False)  # Investment preferences
    step3_complete = Column(BOOLEAN, default=False)  # Scheme selection
    step4_complete = Column(BOOLEAN, default=False)  # Personal information
    step5_complete = Column(BOOLEAN, default=False)  # Address details
    step6_complete = Column(BOOLEAN, default=False)  # Tax residency
    step7_complete = Column(BOOLEAN, default=False)  # Bank details
    step8_complete = Column(BOOLEAN, default=False)  # Nominee details
    step9_complete = Column(BOOLEAN, default=False)  # Mobile verification
    
    # Data storage for each step (JSON fields)
    step1_data = Column(TEXT, nullable=True)  # Personal details & mode
    step2_data = Column(TEXT, nullable=True)  # Investment type
    step3_data = Column(TEXT, nullable=True)  # Selected scheme
    step4_data = Column(TEXT, nullable=True)  # Personal information
    step5_data = Column(TEXT, nullable=True)  # Address details
    step6_data = Column(TEXT, nullable=True)  # Tax residency
    step7_data = Column(TEXT, nullable=True)  # Bank details
    step8_data = Column(TEXT, nullable=True)  # Nominee details
    
    # Registration metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Temporary token for resuming registration
    session_token = Column(String(255), nullable=True, unique=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by_user_id])
    client = relationship("Client", back_populates="registration_state", uselist=False)

    # Add PostgreSQL sequence configuration
    __table_args__ = ()

