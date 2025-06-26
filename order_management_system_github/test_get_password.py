import asyncio
from src.bse_integration.auth import BSEAuthenticator

async def test_get_password():
    try:
        # Initialize BSE authenticator
        auth = BSEAuthenticator()
        
        # Test with a sample passkey
        passkey = "ABCD123456"  # Replace with your actual passkey
        
        print("Attempting to get encrypted password from BSE...")
        response = await auth.authenticate(passkey)
        
        print("\nAuthentication Response:")
        print(f"Success: {response.success}")
        print(f"Status Code: {response.status_code}")
        print(f"Message: {response.message}")
        print(f"Encrypted Password: {response.encrypted_password}")
        print(f"Details: {response.details}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_get_password())
