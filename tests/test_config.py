# Mock BSE settings for testing
class MockBSESettings:
    BSE_USER_ID = "test_user"
    BSE_PASSWORD = "test_pass"
    BSE_MEMBER_CODE = "test_member"
    BSE_BASE_URL = "https://test.bseindia.com"
    BSE_REGISTRATION_PATH = "/test/registration"
    BSE_ORDER_ENTRY_WSDL = "https://test.bseindia.com/wsdl"
    BSE_AUTH_WSDL = "https://test.bseindia.com/wsdl"
    BSE_SESSION_TIMEOUT = 3600

mock_bse_settings = MockBSESettings() 