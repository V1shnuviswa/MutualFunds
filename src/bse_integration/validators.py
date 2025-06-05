"""BSE STAR MF Field Validators

This module contains validation functions for BSE STAR MF fields.
"""

import re
from datetime import datetime
from typing import Optional

class BSEFieldValidationError(Exception):
    """Base exception for BSE field validation errors"""
    pass

def validate_transaction_code(code: str) -> bool:
    """Validate transaction code (3 chars)"""
    valid_codes = {'NEW', 'CXL', 'MOD', 'NEWSIP', 'MODSIP', 'XSIP'}
    if not code or len(code) > 3 or code not in valid_codes:
        raise BSEFieldValidationError(f"Invalid transaction code: {code}")
    return True

def validate_reference_number(ref_no: str) -> bool:
    """Validate unique reference number (19 chars)"""
    pattern = r'^[A-Za-z0-9]{1,19}$'
    if not re.match(pattern, ref_no):
        raise BSEFieldValidationError("Invalid reference number format")
    return True

def validate_member_code(code: str) -> bool:
    """Validate member code (20 chars)"""
    if not code or len(code) > 20:
        raise BSEFieldValidationError("Invalid member code")
    return True

def validate_client_code(code: str) -> bool:
    """Validate client code (20 chars)"""
    if not code or len(code) > 20:
        raise BSEFieldValidationError("Invalid client code")
    return True

def validate_scheme_code(code: str) -> bool:
    """Validate scheme code (20 chars)"""
    if not code or len(code) > 20:
        raise BSEFieldValidationError("Invalid scheme code")
    return True

def validate_pan(pan: Optional[str]) -> bool:
    """Validate PAN number format"""
    if pan:
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        if not re.match(pattern, pan):
            raise BSEFieldValidationError("Invalid PAN format")
    return True

def validate_mobile(mobile: Optional[str]) -> bool:
    """Validate 10-digit mobile number"""
    if mobile:
        pattern = r'^[6-9]\d{9}$'
        if not re.match(pattern, mobile):
            raise BSEFieldValidationError("Invalid mobile number format")
    return True

def validate_email(email: Optional[str]) -> bool:
    """Validate email format"""
    if email:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise BSEFieldValidationError("Invalid email format")
    return True

def validate_date_format(date_str: str) -> bool:
    """Validate date format (DD/MM/YYYY)"""
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        raise BSEFieldValidationError("Invalid date format. Use DD/MM/YYYY")

def validate_amount(amount: str) -> bool:
    """Validate amount format"""
    try:
        float_val = float(amount)
        if float_val <= 0:
            raise BSEFieldValidationError("Amount must be positive")
        return True
    except ValueError:
        raise BSEFieldValidationError("Invalid amount format")

def validate_units(units: str) -> bool:
    """Validate units format"""
    try:
        float_val = float(units)
        if float_val <= 0:
            raise BSEFieldValidationError("Units must be positive")
        return True
    except ValueError:
        raise BSEFieldValidationError("Invalid units format")

def validate_euin(euin: Optional[str]) -> bool:
    """Validate EUIN format"""
    if euin:
        pattern = r'^[A-Z0-9]{1,20}$'
        if not re.match(pattern, euin):
            raise BSEFieldValidationError("Invalid EUIN format")
    return True

def validate_sub_broker_arn(arn: Optional[str]) -> bool:
    """Validate sub-broker ARN"""
    if arn:
        pattern = r'^[A-Z0-9]{1,15}$'
        if not re.match(pattern, arn):
            raise BSEFieldValidationError("Invalid sub-broker ARN format")
    return True

def validate_mandate_id(mandate_id: str) -> bool:
    """Validate mandate ID format"""
    if not mandate_id or len(mandate_id) > 20:
        raise BSEFieldValidationError("Invalid mandate ID")
    return True

def validate_ip_address(ip: Optional[str]) -> bool:
    """Validate IP address format"""
    if ip:
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            raise BSEFieldValidationError("Invalid IP address format")
        # Validate each octet
        octets = ip.split('.')
        if not all(0 <= int(octet) <= 255 for octet in octets):
            raise BSEFieldValidationError("Invalid IP address values")
    return True

def validate_yes_no_flag(flag: str) -> bool:
    """Validate Y/N flag"""
    if flag not in {'Y', 'N'}:
        raise BSEFieldValidationError("Flag must be 'Y' or 'N'")
    return True 