#!/usr/bin/env python3
"""
Test script to verify BSE authentication with real credentials.
This script tests the BSE STAR MF API authentication using real credentials.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Add the current directory to the path so we can import the modules
sys.path.append('.')

from src.bse_integration.auth import BSEAuthenticator
from src.bse_integration.config import bse_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_bse_auth():
    """Test BSE authentication with real credentials."""
    logger.info("Starting BSE authentication test with real credentials")
    logger.info(f"Using BSE User ID: {bse_settings.BSE_USER_ID}")
    logger.info(f"Using BSE Member Code: {bse_settings.BSE_MEMBER_CODE}")
    logger.info(f"Using mock BSE: {bse_settings.USE_MOCK_BSE}")
    
    try:
        # Initialize BSE authenticator
        auth_client = BSEAuthenticator()
        logger.info("BSE authenticator initialized successfully")
        
        # Authenticate with BSE
        passkey = "PassKey123"  # Default passkey
        logger.info(f"Authenticating with passkey: {passkey}")
        
        auth_response = await auth_client.authenticate(passkey)
        logger.info(f"Authentication response: {auth_response}")
        
        if auth_response.success:
            logger.info("Authentication successful!")
            logger.info(f"Encrypted password: {auth_response.encrypted_password}")
            logger.info(f"Session valid until: {auth_client.session_valid_until}")
        else:
            logger.error(f"Authentication failed: {auth_response.message}")
            
        # Test getting encrypted password
        encrypted_password = await auth_client.get_encrypted_password()
        logger.info(f"Got encrypted password: {encrypted_password}")
        
        # Test logout
        auth_client.logout()
        logger.info("Logged out successfully")
        
        return auth_response.success
        
    except Exception as e:
        logger.error(f"Error during BSE authentication test: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("BSE STAR MF Authentication Test")
    logger.info("=" * 50)
    
    start_time = datetime.now()
    success = asyncio.run(test_bse_auth())
    end_time = datetime.now()
    
    logger.info("=" * 50)
    logger.info(f"Test completed in {(end_time - start_time).total_seconds():.2f} seconds")
    logger.info(f"Test result: {'SUCCESS' if success else 'FAILED'}")
    logger.info("=" * 50) 