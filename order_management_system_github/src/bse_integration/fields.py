# fields.py
# Core client registration fields required by BSE STAR MF
CLIENT_REGISTRATION_FIELDS = [
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

