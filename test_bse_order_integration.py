#!/usr/bin/env python
"""
BSE STAR MF Order Integration Test Script
Tests end-to-end order placement with detailed logging and error handling
"""

import asyncio
import logging
import json
from datetime import datetime
import sys
import os
from typing import Dict, Any, Optional

from src.bse_integration.order import BSEOrderPlacer, OrderStatus
from src.bse_integration.auth import BSEAuthenticator
from src.schemas import LumpsumOrderCreate, OrderType, DPTxnMode
from src.bse_integration.exceptions import (
    BSEIntegrationError, BSEAuthError, BSEOrderError,
    BSETransportError, BSESoapFault, BSEValidationError
)

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('bse_order_integration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('bse_order_test')

def monitor_order_status(order_response: Dict[str, Any]) -> None:
    """Log detailed order status information"""
    logger.info("-" * 50)
    logger.info("Order Status Details:")
    logger.info(f"Success: {order_response.success}")
    logger.info(f"Order ID: {order_response.order_id}")
    logger.info(f"Status Code: {order_response.status_code}")
    logger.info(f"Message: {order_response.message}")
    
    if order_response.details:
        logger.info("Additional Details:")
        for key, value in order_response.details.items():
            logger.info(f"  {key}: {value}")
    logger.info("-" * 50)

async def test_lumpsum_order():
    """Test lumpsum order placement with BSE"""
    try:
        # Initialize BSE authenticator
        auth = BSEAuthenticator()
        
        try:
            # Get encrypted password
            logger.info("Getting encrypted password from BSE...")
            encrypted_password = await auth.get_encrypted_password()
            logger.info("Got encrypted password successfully")
        except BSEAuthError as auth_err:
            logger.error(f"Authentication failed: {auth_err}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            raise

        # Create order placer
        order_placer = BSEOrderPlacer()

        # Create test order data with minimum required amount
        order_data = LumpsumOrderCreate(
            transaction_code="NEW",
            unique_ref_no=f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
            client_code="TEST001",
            scheme_code="132LGDG",  # Demo scheme code
            transaction_type=OrderType.PURCHASE,
            buy_sell_type="FRESH",
            dp_txn_mode=DPTxnMode.PHYSICAL,
            amount=5000.00,  # Minimum required amount
            quantity=None,
            all_units_flag=False,
            folio_no="",
            remarks="Integration Test Order",
            kyc_status="Y",
            sub_broker_arn="",
            euin="",
            euin_declaration=False,
            min_redeem=False,
            dpc_flag=False,
            ip_address="127.0.0.1"
        )

        logger.info(f"Placing test lumpsum order with ref no: {order_data.unique_ref_no}")
        logger.debug(f"Order details: {order_data.dict()}")

        try:
            # Place the order
            response = await order_placer.place_lumpsum_order(order_data, encrypted_password)
            
            # Monitor order status
            monitor_order_status(response)
            
            # Check for success
            if response.success:
                logger.info(f"Order placed successfully! Order ID: {response.order_id}")
            else:
                logger.error(f"Order placement failed: {response.message}")
            
            return response

        except BSEValidationError as val_err:
            logger.error(f"Order validation failed: {val_err}")
            raise
        except BSEOrderError as ord_err:
            logger.error(f"Order placement failed: {ord_err}")
            raise
        except BSETransportError as trans_err:
            logger.error(f"Transport error during order placement: {trans_err}")
            raise
        except BSESoapFault as soap_err:
            logger.error(f"SOAP fault during order placement: {soap_err}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during order placement: {e}", exc_info=True)
            raise

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise

async def main():
    """Main entry point with proper error handling"""
    try:
        logger.info("Starting BSE order integration test")
        response = await test_lumpsum_order()
        logger.info("Test completed successfully")
        return response
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
