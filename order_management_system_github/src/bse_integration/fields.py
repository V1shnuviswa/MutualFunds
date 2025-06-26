# fields.py
# Core client registration fields required by BSE STAR MF
CLIENT_REGISTRATION_FIELDS_1 = [
    "ClientCode",                   # 1
    "PrimaryHolderFirstName",       # 2
    "PrimaryHolderMiddleName",      # 3
    "PrimaryHolderLastName",        # 4
    "TaxStatus",                    # 5
    "Gender",                       # 6
    "PrimaryHolderDOB",             # 7
    "OccupationCode",               # 8
    "HoldingNature",                # 9
    "DividendPayMode",              # 10
    "SecondHolderFirstName",        # 11
    "SecondHolderMiddleName",       # 12
    "SecondHolderLastName",         # 13
    "ThirdHolderFirstName",         # 14
    "ThirdHolderMiddleName",        # 15
    "ThirdHolderLastName",          # 16
    "SecondHolderDOB",              # 17
    "ThirdHolderDOB",               # 18
    "GuardianFirstName",            # 19
    "GuardianMiddleName",           # 20
    "GuardianLastName",             # 21
    "GuardianDOB",                  # 22
    "PrimaryHolderPANExempt",       # 23
    "SecondHolderPANExempt",        # 24
    "ThirdHolderPANExempt",         # 25
    "GuardianPANExempt",            # 26
    "PrimaryHolderPAN",             # 27
    "SecondHolderPAN",              # 28
    "ThirdHolderPAN",               # 29
    "GuardianPAN",                  # 30
    "PrimaryHolderExemptCategory",  # 31
    "SecondHolderExemptCategory",   # 32
    "ThirdHolderExemptCategory",    # 33
    "GuardianExemptCategory",       # 34
    "ClientType",                   # 35
    "PMS",                          # 36
    "DefaultDP",                    # 37
    "CDSLDPID",                     # 38
    "CDSLCLTID",                    # 39
    "CMBPId",                       # 40
    "NSDLDPID",                     # 41
    "NSDLCLTID",                    # 42
    "AccountType1",                 # 43
    "AccountNo1",                   # 44
    "MICRNo1",                      # 45
    "IFSCCode1",                    # 46
    "DefaultBankFlag1",             # 47
    "AccountType2",                 # 48
    "AccountNo2",                   # 49
    "MICRNo2",                      # 50
    "IFSCCode2",                    # 51
    "DefaultBankFlag2",             # 52
    "AccountType3",                 # 53
    "AccountNo3",                   # 54
    "MICRNo3",                      # 55
    "IFSCCode3",                    # 56
    "DefaultBankFlag3",             # 57
    "AccountType4",                 # 58
    "AccountNo4",                   # 59
    "MICRNo4",                      # 60
    "IFSCCode4",                    # 61
    "DefaultBankFlag4",             # 62
    "AccountType5",                 # 63
    "AccountNo5",                   # 64
    "MICRNo5",                      # 65
    "IFSCCode5",                    # 66
    "DefaultBankFlag5",             # 67
    "ChequeName",                   # 68
    "Address1",                     # 69
    "Address2",                     # 70
    "Address3",                     # 71
    "City",                         # 72
    "State",                        # 73
    "Pincode",                      # 74
    "Country",                      # 75
    "ResiPhone",                    # 76
    "ResiFax",                      # 77
    "OfficePhone",                  # 78
    "OfficeFax",                    # 79
    "Email",                        # 80
    "CommunicationMode",            # 81
    "ForeignAddress1",              # 82
    "ForeignAddress2",              # 83
    "ForeignAddress3",              # 84
    "ForeignAddressCity",           # 85
    "ForeignAddressPincode",        # 86
    "ForeignAddressState",          # 87
    "ForeignAddressCountry",        # 88
    "ForeignAddressResiPhone",      # 89
    "ForeignAddressFax",            # 90
    "ForeignAddressOffPhone",       # 91
    "ForeignAddressOffFax",         # 92
    "IndianMobileNo",               # 93
    "Nominee1Name",                 # 94
    "Nominee1Relationship",         # 95
    "Nominee1Percentage",           # 96
    "Nominee1MinorFlag",            # 97
    "Nominee1DOB",                  # 98
    "Nominee1Guardian",             # 99
    "Nominee2Name",                 # 100
    "Nominee2Relationship",         # 101
    "Nominee2Percentage",           # 102
    "Nominee2DOB",                  # 103
    "Nominee2MinorFlag",            # 104
    "Nominee2Guardian",             # 105
    "Nominee3Name",                 # 106
    "Nominee3Relationship",         # 107
    "Nominee3Percentage",           # 108
    "Nominee3DOB",                  # 109
    "Nominee3MinorFlag",            # 110
    "Nominee3Guardian",             # 111
    "PrimaryHolderKYCType",         # 112
    "PrimaryHolderCKYCNumber",      # 113
    "SecondHolderKYCType",          # 114
    "SecondHolderCKYCNumber",       # 115
    "ThirdHolderKYCType",           # 116
    "ThirdHolderCKYCNumber",        # 117
    "GuardianKYCType",              # 118
    "GuardianCKYCNumber",           # 119
    "PrimaryHolderKRAExemptRefNo",  # 120
    "SecondHolderKRAExemptRefNo",   # 121
    "ThirdHolderKRAExemptRefNo",    # 122
    "GuardianKRAExemptRefNo",       # 123
    "AadhaarUpdated",               # 124
    "MapinId",                      # 125
    "PaperlessFlag",                # 126
    "LEINo",                        # 127
    "LEIValidity",                  # 128
    "MobileDeclarationFlag",        # 129
    "EmailDeclarationFlag",         # 130
    "Filler3"                       # 131
]

# Minimum required fields for basic client registration
MINIMUM_REQUIRED_FIELDS = [
    "ClientCode",
    "PrimaryHolderFirstName",
    "TaxStatus",
    "Gender",
    "PrimaryHolderDOB",
    "OccupationCode",
    "HoldingNature",
    "DividendPayMode",
    "PrimaryHolderPANExempt",
    "AccountType1",
    "AccountNo1",
    "MICRNo1",
    "IFSCCode1",
    "DefaultBankFlag1",
    "Address1",
    "City",
    "State",
    "Pincode",
    "Country",
    "Email",
    "CommunicationMode",
    "MobileDeclarationFlag",
    "EmailDeclarationFlag"
]

CLIENT_REGISTRATION_FIELDS = {
    "ClientCode": "",  # Mandatory
    "PrimaryHolderFirstName": "",  # Mandatory
    "PrimaryHolderMiddleName": "",  # Optional
    "PrimaryHolderLastName": "",  # Optional
    "TaxStatus": "",  # Mandatory
    "Gender": "",  # Mandatory for Individual, NRI and Minor clients
    "PrimaryHolderDOB": "",  # Mandatory (DD/MM/YYYY)
    "OccupationCode": "",  # Mandatory 01/02/03/04/05/06/07/08/09/10
    "HoldingNature": "",  # Mandatory SI/JO/AS
    "SecondHolderFirstName": "",  # Conditional Mandatory if Mode of Holding is JO/AS
    "SecondHolderMiddleName": "",  # Optional
    "SecondHolderLastName": "",  # Conditional Mandatory if Mode of Holding is JO/AS
    "ThirdHolderFirstName": "",  # Optional
    "ThirdHolderMiddleName": "",  # Optional
    "ThirdHolderLastName": "",  # Optional; Mandatory if First Name mentioned
    "SecondHolderDOB": "",  # Conditional Mandatory if Holding is JO/AS
    "ThirdHolderDOB": "",  # Conditional Mandatory if Third holder present
    "GuardianFirstName": "",  # Conditional Mandatory for Minor investment
    "GuardianMiddleName": "",  # Conditional Mandatory for Minor investment
    "GuardianLastName": "",  # Conditional Mandatory for Minor investment
    "GuardianDOB": "",  # Optional; Mandatory for Minor clients (DD/MM/YYYY)
    "PrimaryHolderPANExempt": "",  # Mandatory
    "SecondHolderPANExempt": "",  # Mandatory if Joint holding and name provided
    "ThirdHolderPANExempt": "",  # Mandatory if Third Holder name provided
    "GuardianPANExempt": "",  # Conditional Mandatory for Minor clients
    "PrimaryHolderPAN": "",  # Conditional Mandatory if PAN Exempt = N
    "SecondHolderPAN": "",  # Conditional Mandatory if PAN Exempt = N and name provided
    "ThirdHolderPAN": "",  # Conditional Mandatory if PAN Exempt = N and name provided
    "GuardianPAN": "",  # Conditional Mandatory if Guardian name is provided
    "PrimaryExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "SecondExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "ThirdExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "GuardianExemptCategory": "",  # Conditional Mandatory if PAN Exempt = Y
    "ClientType": "",  # Mandatory (D/P)
    "PMS": "",  # Optional (Y/N)
    "DefaultDP": "",  # Conditional Mandatory if ClientType = D CDSL/NSDL
    "CDSLDPID": "",  # Conditional Mandatory if Default DP = CDSL
    "CDSLCLTID": "",  # Conditional Mandatory if Default DP = CDSL
    "CMBPID": "",  # Conditional Mandatory if PMS = Y and DP = NSDL
    "NSDLDPID": "",  # Conditional Mandatory if Default DP = NSDL
    "NSDLCLTID": "",  # Conditional Mandatory if Default DP = NSDL
    "AccountType1": "",  # Mandatory (SB/CB/NE/NO)
    "AccountNo1": "",  # Mandatory
    "MICRNo1": "",  # Optional
    "IFSCCode1": "",  # Mandatory
    "DefaultBankFlag1": "",  # Mandatory (Y/N)
    "AccountType2": "",  # Optional
    "AccountNo2": "",  # Conditional Mandatory if present
    "MICRNo2": "",  # Optional
    "IFSCCode2": "",  # Conditional Mandatory if present
    "DefaultBankFlag2": "",  # Conditional Mandatory if present
    "AccountType3": "",  # Optional
    "AccountNo3": "",  # Conditional Mandatory if present
    "MICRNo3": "",  # Optional
    "IFSCCode3": "",  # Conditional Mandatory if present
    "DefaultBankFlag3": "",  # Conditional Mandatory if present
    "AccountType4": "",  # Optional
    "AccountNo4": "",  # Conditional Mandatory if present
    "MICRNo4": "",  # Optional
    "IFSCCode4": "",  # Conditional Mandatory if present
    "DefaultBankFlag4": "",  # Conditional Mandatory if present
    "AccountType5": "",  # Optional
    "AccountNo5": "",  # Conditional Mandatory if present
    "MICRNo5": "",  # Optional
    "IFSCCode5": "",  # Conditional Mandatory if present
    "DefaultBankFlag5": "",  # Conditional Mandatory if present
    "ChequeName": "",  # Optional
    "DividendPayMode": "",  # Mandatory (01 = Reinvest, 02 = Payout, 03 = Switch, 04 = Direct Credit, 05 = NEFT/RTGS, 06 = ECS, 07 = NACH, 08 = Auto Sweep, 09 = Systematic Transfer Plan)
    "Address1": "",  # Mandatory
    "Address2": "",  # Optional
    "Address3": "",  # Optional
    "City": "",  # Mandatory
    "State": "",  # Mandatory
    "Pincode": "",  # Mandatory
    "Country": "",  # Mandatory
    "ResPhone": "",  # Optional
    "ResFax": "",  # Optional
    "OffPhone": "",  # Optional
    "OffFax": "",  # Optional
    "Email": "",  # Mandatory
    "CommunicationMode": "",  # Mandatory P-Physical, E-Email, M-Mobile
    "ForeignAddress1": "",  # Conditional Mandatory for NRI
    "ForeignAddress2": "",  # Optional
    "ForeignAddress3": "",  # Optional
    "ForeignCity": "",  # Conditional Mandatory for NRI
    "ForeignPincode": "",  # Conditional Mandatory for NRI
    "ForeignState": "",  # Conditional Mandatory for NRI
    "ForeignCountry": "",  # Conditional Mandatory for NRI
    "ForeignResPhone": "",  # Optional
    "ForeignResFax": "",  # Optional
    "ForeignOffPhone": "",  # Optional
    "ForeignOffFax": "",  # Optional
    "IndianMobile": "",  # Mandatory
    "PrimaryHolderKYCType": "",  # Mandatory (K/C/B/E)
    "PrimaryHolderCKYC": "",  # Conditional Mandatory if KYC Type = C
    "SecondHolderKYCType": "",  # Optional
    "SecondHolderCKYC": "",  # Conditional Mandatory if KYC Type = C
    "ThirdHolderKYCType": "",  # Optional
    "ThirdHolderCKYC": "",  # Conditional Mandatory if KYC Type = C
    "GuardianKYCType": "",  # Optional
    "GuardianCKYC": "",  # Conditional Mandatory if KYC Type = C and Minor
    "PrimaryHolderKRAExemptRefNo": "",  # Conditional Mandatory if Primary Holder PAN Exempt
    "SecondHolderKRAExemptRefNo": "",  # Conditional Mandatory if Second Holder PAN Exempt
    "ThirdHolderKRAExemptRefNo": "",  # Conditional Mandatory if Third Holder PAN Exempt
    "GuardianExemptRefNo": "",  # Conditional Mandatory if Guardian PAN Exempt
    "AadhaarUpdated": "",  # Optional (Y/N)
    "MapinId": "",  # Optional
    "PaperlessFlag": "",  # Mandatory; P = Paper, Z = Paperless
    "LEINo": "",  # Optional
    "LEIValidity": "",  # Conditional Mandatory (DD/MM/YYYY)
    "MobileDeclarationFlag": "",  # Conditional Mandatory if Mobile No. provided
    "EmailDeclarationFlag": "",  # Conditional Mandatory if Email Id provided
    "SecondHolderEmail": "",  # Mandatory if Mode of Holding is JO/AS
    "SecondHolderEmailDeclaration": "",  # Conditional Mandatory if Email provided
    "SecondHolderMobile": "",  # Mandatory if Mode of Holding is JO/AS
    "SecondHolderMobileDeclaration": "",  # Conditional Mandatory if Mobile No. provided
    "ThirdHolderEmail": "",  # Mandatory if Third Holder is present
    "ThirdHolderEmailDeclaration": "",  # Conditional Mandatory if Email provided
    "ThirdHolderMobile": "",  # Mandatory if Third Holder is present
    "ThirdHolderMobileDeclaration": "",  # Conditional Mandatory if Mobile No. provided
    "GuardianRelationship": "",  # Conditional Mandatory; 23 - FATHER, 24 - MOTHER, etc.
    "NominationOpt": "",  # Optional for Demat; Mandatory for Non-Demat SI Holding
    "NominationAuthMode": "",  # Optional; W = Wet, E = eSign, O = OTP
    "Nominee1Name": "",  # Conditional Mandatory if NominationOpt = Y
    "Nominee1Relationship": "",  # Conditional Mandatory if Nominee present
    "Nominee1ApplicablePercent": "",  # Conditional Mandatory if Nominee present
    "Nominee1MinorFlag": "",  # Conditional Mandatory if Nominee present
    "Nominee1DOB": "",  # Conditional Mandatory if MinorFlag = Y
    "Nominee1Guardian": "",  # Optional
    "Nominee1GuardianPAN": "",  # Optional
    "Nominee1IdentityType": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1IDNumber": "",  # Conditional Mandatory if ID Type provided
    "Nominee1Email": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Mobile": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Address1": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Address2": "",  # Optional
    "Nominee1Address3": "",  # Optional
    "Nominee1City": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Pincode": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee1Country": "",  # Conditional Mandatory if NomineeOpt = Y
    "Nominee2Name": "",  # Conditional Mandatory if Nominee1 < 100%
    "Nominee2Relationship": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2ApplicablePercent": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2MinorFlag": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2DOB": "",  # Conditional Mandatory if Nominee2 available
    "Nominee2Guardian": "",  # Optional
    "Nominee2GuardianPAN": "",  # Optional
    "Nominee2IdentityType": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2IDNumber": "",  # Conditional Mandatory based on ID Type
    "Nominee2Email": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Mobile": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Address1": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Address2": "",  # Optional
    "Nominee2Address3": "",  # Optional
    "Nominee2City": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Pincode": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee2Country": "",  # Conditional Mandatory if Nominee2 Opted
    "Nominee3Name": "",  # Conditional Mandatory if % < 100%
    "Nominee3Relationship": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3ApplicablePercent": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3MinorFlag": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3DOB": "",  # Conditional Mandatory if Nominee3 available
    "Nominee3Guardian": "",  # Optional
    "Nominee3GuardianPAN": "",  # Optional
    "Nominee3IdentityType": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3IDNumber": "",  # Conditional Mandatory based on ID Type
    "Nominee3Email": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Mobile": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Address1": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Address2": "",  # Optional
    "Nominee3Address3": "",  # Optional
    "Nominee3City": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Pincode": "",  # Conditional Mandatory if Nominee3 Opted
    "Nominee3Country": "",  # Conditional Mandatory if Nominee3 Opted
    "NomineeSOAFlag": "",  # Mandatory if NomineeOpt = Y; Y/N display in SOA
    "Filler1": "",  # Optional
    "Filler2": "",  # Optional
    "Filler3": "",  # Optional
    "Filler4": "",  # Optional
    "Filler5": "",  # Optional
    "Filler6": "",  # Optional
    "Filler7": "",  # Optional
    "Filler8": "",  # Optional
}