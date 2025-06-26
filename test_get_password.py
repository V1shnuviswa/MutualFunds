import asyncio
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.bse_integration.auth import BSEAuthenticator
from src.bse_integration.config import bse_settings

async def test_get_password():
    try:
        # Initialize BSE authenticator
        auth = BSEAuthenticator()
        
        # Use the passkey from config
        passkey = bse_settings.BSE_PASSKEY
        
        print("\nBSE Authentication Test")
        print("----------------------")
        print(f"Using PassKey: {passkey}")
        print(f"User ID: {bse_settings.BSE_USER_ID}")
        print(f"Member Code: {bse_settings.BSE_MEMBER_CODE}")
        print("\nStep 1: Initial Authentication")
        print("Attempting to get encrypted password from BSE...")
        
        response = await auth.authenticate(passkey)
        
        print("\nAuthentication Response:")
        print(f"Success: {response.success}")
        print(f"Status Code: {response.status_code}")
        print(f"Message: {response.message}")
        if response.success:
            print(f"Encrypted Password: {response.encrypted_password}")
            print(f"Session Valid Until: {auth.session_valid_until}")
        print(f"Details: {response.details}")
        
        if response.success:
            print("\nStep 2: Testing Password Caching")
            print("Getting encrypted password again...")
            cached_password = await auth.get_encrypted_password()
            print(f"Cached Password Matches: {cached_password == response.encrypted_password}")
            
            print("\nStep 3: This is the password that would be used in lumpsum order")
            print(f"Password to use in order: {cached_password}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_password())
