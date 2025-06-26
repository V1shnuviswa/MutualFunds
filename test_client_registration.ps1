# PowerShell script to test BSE client registration flow

Write-Host "Step 1: Getting access token..."
$tokenResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/login" `
    -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
    -Body "username=6385101&password=Abc@1234"

$accessToken = $tokenResponse.access_token
Write-Host "Access Token: $accessToken"

# Client data for code generation
$clientNameData = @{
    PrimaryHolderFirstName = "John"
    PrimaryHolderLastName = "Doe"
    PrimaryHolderDOB = "01/01/1990"  # Changed from DOB to PrimaryHolderDOB
} | ConvertTo-Json

Write-Host "`nStep 2: Generating client code..."
$codeResponse = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/bse/clients/generate-code" `
    -Headers @{
        "Content-Type"="application/json"
        "Authorization"="Bearer $accessToken"
    } `
    -Body $clientNameData

$clientCode = $codeResponse.client_code
Write-Host "Generated Client Code: $clientCode"

# Create unique client code if not generated
if (-not $clientCode) {
    $clientCode = "DTJOHNDOE$(Get-Date -Format 'yyyyMMdd')"
    Write-Host "Using fallback client code: $clientCode"
}

Write-Host "`nStep 3: Registering client with BSE..."
# Use minimal set of fields for testing
$clientData = @{
    # Required fields in the correct order
    ClientCode = "0100000111"
    PrimaryHolderFirstName = "Vishnu"
    PrimaryHolderMiddleName = ""
    PrimaryHolderLastName = "Viswa"
    TaxStatus = "01"                     # Individual
    Gender = "M"
    PrimaryHolderDOB = "06/09/2004"      # Changed from DOB to PrimaryHolderDOB
    OccupationCode = "01"                # Business
    HoldingNature = "SI"                 # Single
    DividendPayMode = "01"               # Reinvest
    PrimaryHolderPANExempt = "N"
    PrimaryHolderPAN = "ABCDE1234F"
    ClientType = "P"                     # Physical
    AccountType1 = "SB"                  # Savings Bank
    AccountNo1 = "12345678901"
    IFSCCode1 = "HDFC0000001"
    DefaultBankFlag1 = "Y"
    Address1 = "123 Main Street"
    City = "Mumbai"
    State = "Maharashtra"
    Pincode = "400001"
    Country = "India"
    Email = "vishnuviswa1970@gmail.com"
    CommunicationMode = "E"              # Email
    IndianMobile = "7010598418"
    PrimaryHolderKYCType = "K"           # KYC
    PaperlessFlag = "Z"                  # Paperless
    MobileDeclarationFlag = "Y"
    EmailDeclarationFlag = "Y"
} | ConvertTo-Json

Write-Host "Client data being sent:"
Write-Host $clientData

try {
    $response = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/bse/clients/register" `
        -Headers @{
            "Content-Type"="application/json"
            "Authorization"="Bearer $accessToken"
        } `
        -Body $clientData

    Write-Host "`nRegistration successful!"
    Write-Host "Status: $($response.status)"
    Write-Host "Message: $($response.message)"
    Write-Host "Client Code: $($response.client_code)"
    
    if ($response.details) {
        Write-Host "`nResponse details:"
        Write-Host "Status: $($response.details.Status)"
        Write-Host "Remarks: $($response.details.Remarks)"
    }
} catch {
    Write-Host "`nError occurred:"
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)"
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)"
    
    $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
    $reader.BaseStream.Position = 0
    $reader.DiscardBufferedData()
    $responseBody = $reader.ReadToEnd()
    Write-Host "Error Details: $responseBody"
}

# Note: The server will:
# 1. Validate your access token
# 2. Validate the client data
# 3. Send the client registration request to BSE
# 4. Return the response from BSE 