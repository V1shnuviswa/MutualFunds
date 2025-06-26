"""
BSE UCC Registration Template

This module provides a template with all 183 fields required by BSE for client registration.
"""

from collections import OrderedDict

# Create a template with all 183 fields required by BSE
def create_ucc_template(client_data=None):
    """
    Create a template with all 183 fields required by BSE for client registration.
    
    Args:
        client_data: Optional dictionary with client data to pre-fill the template
        
    Returns:
        OrderedDict with all 183 fields required by BSE
    """
    # Start with the fields defined in CLIENT_REGISTRATION_FIELDS
    from .fields import CLIENT_REGISTRATION_FIELDS
    
    # Create an OrderedDict to maintain field order
    template = OrderedDict()
    
    # Copy all fields from CLIENT_REGISTRATION_FIELDS
    for field, default_value in CLIENT_REGISTRATION_FIELDS.items():
        template[field] = default_value
    
    # If client_data is provided, update the template with client data
    if client_data:
        for field, value in client_data.items():
            if field in template:
                template[field] = value
    
    # Ensure we have exactly 183 fields
    if len(template) < 183:
        # Add filler fields if needed
        for i in range(9, 183 - len(template) + 1):
            template[f"Filler{i}"] = ""
    
    # Verify we have exactly 183 fields
    assert len(template) == 183, f"Template has {len(template)} fields, but BSE requires exactly 183 fields."
    
    return template

# Create a minimal template with only the required fields
def create_minimal_template():
    """
    Create a minimal template with only the required fields.
    
    Returns:
        OrderedDict with minimal required fields
    """
    from .fields import MINIMUM_REQUIRED_FIELDS
    
    # Create an OrderedDict to maintain field order
    template = OrderedDict()
    
    # Set minimal required fields
    template["ClientCode"] = ""
    template["PrimaryHolderFirstName"] = ""
    template["PrimaryHolderMiddleName"] = ""
    template["PrimaryHolderLastName"] = ""
    template["TaxStatus"] = "01"  # Individual
    template["Gender"] = "M"
    template["PrimaryHolderDOB"] = ""  # DD/MM/YYYY
    template["OccupationCode"] = "01"  # Business
    template["HoldingNature"] = "SI"  # Single
    template["DividendPayMode"] = "01"  # Reinvest
    template["PrimaryHolderPANExempt"] = "N"
    template["PrimaryHolderPAN"] = ""
    template["ClientType"] = "P"  # Physical
    template["AccountType1"] = "SB"  # Savings
    template["AccountNo1"] = ""
    template["IFSCCode1"] = ""
    template["DefaultBankFlag1"] = "Y"
    template["Address1"] = ""
    template["City"] = ""
    template["State"] = ""
    template["Pincode"] = ""
    template["Country"] = "India"
    template["Email"] = ""
    template["CommunicationMode"] = "E"  # Email
    template["IndianMobile"] = ""
    template["PrimaryHolderKYCType"] = "K"  # KYC
    template["PaperlessFlag"] = "Z"  # Paperless
    
    # Fill the rest with empty strings to get to 183 fields
    return create_ucc_template(template)

def map_client_to_bse_format(client_data):
    """
    Map client data to BSE format.
    
    Args:
        client_data: Dictionary with client data
        
    Returns:
        OrderedDict with client data in BSE format
    """
    # Create a template
    template = create_ucc_template()
    
    # Map client data to BSE format
    if client_data.get("client_name"):
        names = client_data["client_name"].split()
        template["PrimaryHolderFirstName"] = names[0]
        if len(names) > 1:
            template["PrimaryHolderLastName"] = names[-1]
    
    if client_data.get("client_code"):
        template["ClientCode"] = client_data["client_code"]
    
    if client_data.get("pan"):
        template["PrimaryHolderPAN"] = client_data["pan"]
        template["PrimaryHolderPANExempt"] = "N"
    
    if client_data.get("email"):
        template["Email"] = client_data["email"]
    
    if client_data.get("mobile"):
        template["IndianMobile"] = client_data["mobile"]
    
    if client_data.get("date_of_birth"):
        # Convert to DD/MM/YYYY format if needed
        from datetime import datetime
        try:
            if isinstance(client_data["date_of_birth"], datetime):
                template["PrimaryHolderDOB"] = client_data["date_of_birth"].strftime("%d/%m/%Y")
            else:
                template["PrimaryHolderDOB"] = client_data["date_of_birth"]
        except:
            template["PrimaryHolderDOB"] = client_data["date_of_birth"]
    
    if client_data.get("address"):
        template["Address1"] = client_data["address"]
    
    if client_data.get("city"):
        template["City"] = client_data["city"]
    
    if client_data.get("state"):
        template["State"] = client_data["state"]
    
    if client_data.get("pincode"):
        template["Pincode"] = client_data["pincode"]
    
    if client_data.get("country"):
        template["Country"] = client_data["country"]
    
    if client_data.get("bank_account_number"):
        template["AccountNo1"] = client_data["bank_account_number"]
    
    if client_data.get("ifsc_code"):
        template["IFSCCode1"] = client_data["ifsc_code"]
    
    # Return the template with client data
    return template 