# PowerShell script to test lumpsum order flow

Write-Host "Step 1: Getting access token..."
$tokenResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" `
    -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
    -Body "username=6385101&password=Abc@1234"

$accessToken = $tokenResponse.access_token
Write-Host "Access Token: $accessToken"

Write-Host "`nStep 2: Getting encrypted password from BSE..."
$encryptedPasswordResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/get_encrypted_password" `
    -Headers @{
        "Content-Type"="application/json"
        "Authorization"="Bearer $accessToken"
    } `
    -Body (@{ passKey = "PassKey123" } | ConvertTo-Json)

$encryptedPassword = $encryptedPasswordResponse.encrypted_password
Write-Host "Encrypted Password: $encryptedPassword"

$memberId = "63851"
$transNo = "$(Get-Date -Format 'yyyyMMdd')$memberId$(Get-Random -Minimum 1000 -Maximum 9999)"


Write-Host "`nStep 3: Placing lumpsum order..."
$orderBody = @{
    # Mandatory fields
    TransCode = "NEW"                    # Mandatory (NEW/MOD/CXL)
    TransNo = $transNo     # Mandatory (YYYYMMDDmemberid000001)
    RefNo = "$((Get-Date).ToString('MMddHHmmss'))REF63851"    # Exactly 20 chars: MMddHHmmss(10) + REF(3) + 638510001(7)
    UserID = "6385101"                   # Mandatory (BSE User ID)
    MemberId = "63851"                   # Mandatory (BSE Member ID)
    ClientCode = "0000000011"            # Mandatory
    SchemeCd = "EDWRG"              # Mandatory
    BuySell = "P"                        # Mandatory (P/R)
    BuySellType = "FRESH"               # Mandatory (FRESH/ADDITIONAL)
    DPTxn = "P"                         # Mandatory (C/N/P)
    Amount = 1000.00                   # Either Amount or Qty is mandatory
    AllRedeem = "N"                     # Mandatory (Y/N)
    KYCStatus = "Y"                     # Mandatory (Y/N)
    EUINVal = "Y"                      # Mandatory (Y/N) - Must be Y when EUIN is provided
    MinRedeem = "N"                     # Mandatory (Y/N)
    DPC = "Y"                          # Mandatory (Y)
    IPAdd = ""                # Mandatory
    Password = $encryptedPassword       # Mandatory
    PassKey = "PassKey123"             # Mandatory

    # Optional fields with empty strings

    FolioNo = ""                # Mandatory (For Physical Additional)
    Remarks = ""                       # Optional
    SubBrokerARN = ""                 # Optional
    EUIN = "E543938"                  # Mandatory
    MobileNo = "7010598418"                     # Optional
    EmailID = "vishnuviswa1970@gmail.com"                      # Optional
    MandateID = ""                    # Optional
} | ConvertTo-Json

$response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/orders/lumpsum" `
    -Headers @{
        "Content-Type"="application/json"
        "Authorization"="Bearer $accessToken"
    } `
    -Body $orderBody

Write-Host "Response:"
$response | ConvertTo-Json

# Note: The server will:
# 1. Validate your access token
# 2. Use BSEAuthenticator to get encrypted password from BSE using:
#    - BSE_USER_ID: 6385101
#    - BSE_PASSWORD: Abc@1234
#    - BSE_PASSKEY: PassKey123
# 3. Create SOAP request with all required fields including the encrypted password
# 4. Send request to BSE
