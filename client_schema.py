from pydantic import BaseModel, Field, validator, EmailStr, constr
from typing import Optional
from datetime import date
import re
from enum import Enum

class Gender(str, Enum):
    MALE = 'M'
    FEMALE = 'F'
    TRANSGENDER = 'T'
    OTHER = 'O'

class AccountType(str, Enum):
    SAVINGS = 'SB'
    CURRENT = 'CB'
    NRE = 'NE'
    NRO = 'NO'

class CommunicationMode(str, Enum):
    PHYSICAL = 'P'
    ELECTRONIC = 'E'
    MOBILE = 'M'

class HoldingNature(str, Enum):
    SINGLE = 'SI'
    JOINT = 'JO'
    ANYONE_SURVIVOR = 'AS'

class DividendPayMode(str, Enum):
    CHEQUE = '01'
    DIRECT_CREDIT = '02'
    ECS = '03'
    NEFT = '04'
    RTGS = '05'

class OccupationCode(str, Enum):
    BUSINESS = '01'
    SERVICES = '02'
    PROFESSIONAL = '03'
    AGRICULTURE = '04'
    RETIRED = '05'
    HOUSEWIFE = '06'
    STUDENT = '07'
    OTHERS = '08'

class PANExemptCategory(str, Enum):
    SIKKIM_RESIDENT = '01'
    STATE_GOVT = '02'
    CENTRAL_GOVT = '03'
    COURT_APPOINTED_OFFICIALS = '04'
    UN_ENTITY = '05'
    OFFICIAL_LIQUIDATOR = '06'
    COURT_RECEIVER = '07'
    MUTUAL_FUNDS_UPTO_50K = '08'

class StateCode(str, Enum):
    ANDAMAN_NICOBAR = 'AN'
    ARUNACHAL_PRADESH = 'AR'
    ANDHRA_PRADESH = 'AP'
    ASSAM = 'AS'
    BIHAR = 'BH'
    CHANDIGARH = 'CH'
    CHHATTISGARH = 'CG'
    GOA = 'GO'
    GUJARAT = 'GU'
    HARYANA = 'HA'
    HIMACHAL_PRADESH = 'HP'
    JAMMU_KASHMIR = 'JM'
    JHARKHAND = 'JK'
    KARNATAKA = 'KA'
    KERALA = 'KE'
    MADHYA_PRADESH = 'MP'
    MAHARASHTRA = 'MA'
    MANIPUR = 'MN'
    MEGHALAYA = 'ME'
    MIZORAM = 'MI'
    NAGALAND = 'NA'
    NEW_DELHI = 'ND'
    ORISSA = 'OR'
    PONDICHERRY = 'PO'
    PUNJAB = 'PU'
    RAJASTHAN = 'RA'
    SIKKIM = 'SI'
    TELANGANA = 'TG'
    TAMIL_NADU = 'TN'
    TRIPURA = 'TR'
    UTTAR_PRADESH = 'UP'
    UTTARANCHAL = 'UC'
    WEST_BENGAL = 'WB'
    DADRA_NAGAR_HAVELI = 'DN'
    DAMAN_DIU = 'DD'
    LAKSHADWEEP = 'LD'
    OTHERS = 'OH'

class CountryCode(str, Enum):
    AFGHANISTAN = '001'
    ALAND_ISLANDS = '002'
    ALBANIA = '003'
    ALGERIA = '004'
    AMERICAN_SAMOA = '005'
    ANDORRA = '006'
    ANGOLA = '007'
    ANGUILLA = '008'
    ANTARCTICA = '009'
    ANTIGUA_AND_BARBUDA = '010'
    ARGENTINA = '011'
    ARMENIA = '012'
    ARUBA = '013'
    AUSTRALIA = '014'
    AUSTRIA = '015'
    AZERBAIJAN = '016'
    BAHAMAS = '017'
    BAHRAIN = '018'
    BANGLADESH = '019'
    BARBADOS = '020'
    BELARUS = '021'
    BELGIUM = '022'
    BELIZE = '023'
    BENIN = '024'
    BERMUDA = '025'
    BHUTAN = '026'
    BOLIVIA = '027'
    BOSNIA_AND_HERZEGOVINA = '028'
    BOTSWANA = '029'
    BOUVET_ISLAND = '030'
    BRAZIL = '031'
    BRITISH_INDIAN_OCEAN_TERRITORY = '032'
    BRUNEI_DARUSSALAM = '033'
    BULGARIA = '034'
    BURKINA_FASO = '035'
    BURUNDI = '036'
    CAMBODIA = '037'
    CAMEROON = '038'
    CANADA = '039'
    CAPE_VERDE = '040'
    CAYMAN_ISLANDS = '041'
    CENTRAL_AFRICAN_REPUBLIC = '042'
    CHAD = '043'
    CHILE = '044'
    CHINA = '045'
    CHRISTMAS_ISLAND = '046'
    COCOS_KEELING_ISLANDS = '047'
    COLOMBIA = '048'
    COMOROS = '049'
    CONGO = '050'
    CONGO_DEMOCRATIC_REPUBLIC = '051'
    COOK_ISLANDS = '052'
    COSTA_RICA = '053'
    COTE_DIVOIRE = '054'
    CROATIA = '055'
    CUBA = '056'
    CYPRUS = '057'
    CZECH_REPUBLIC = '058'
    DENMARK = '059'
    DJIBOUTI = '060'
    DOMINICA = '061'
    DOMINICAN_REPUBLIC = '062'
    ECUADOR = '063'
    EGYPT = '064'
    EL_SALVADOR = '065'
    EQUATORIAL_GUINEA = '066'
    ERITREA = '067'
    ESTONIA = '068'
    ETHIOPIA = '069'
    FALKLAND_ISLANDS = '070'
    FAROE_ISLANDS = '071'
    FIJI = '072'
    FINLAND = '073'
    FRANCE = '074'
    FRENCH_GUIANA = '075'
    FRENCH_POLYNESIA = '076'
    FRENCH_SOUTHERN_TERRITORIES = '077'
    GABON = '078'
    GAMBIA = '079'
    GEORGIA = '080'
    GERMANY = '081'
    GHANA = '082'
    GIBRALTAR = '083'
    GREECE = '084'
    GREENLAND = '085'
    GRENADA = '086'
    GUADELOUPE = '087'
    GUAM = '088'
    GUATEMALA = '089'
    GUERNSEY = '090'
    GUINEA = '091'
    GUINEA_BISSAU = '092'
    GUYANA = '093'
    HAITI = '094'
    HEARD_ISLAND_AND_MCDONALD_ISLANDS = '095'
    HOLY_SEE = '096'
    HONDURAS = '097'
    HONG_KONG = '098'
    HUNGARY = '099'
    ICELAND = '100'
    INDIA = '101'
    INDONESIA = '102'
    IRAN = '103'
    IRAQ = '104'
    IRELAND = '105'
    ISLE_OF_MAN = '106'
    ISRAEL = '107'
    ITALY = '108'
    JAMAICA = '109'
    JAPAN = '110'
    JERSEY = '111'
    JORDAN = '112'
    KAZAKHSTAN = '113'
    KENYA = '114'
    KIRIBATI = '115'
    KOREA_DEMOCRATIC_PEOPLES_REPUBLIC = '116'
    KOREA_REPUBLIC = '117'
    KUWAIT = '118'
    KYRGYZSTAN = '119'
    LAO_PEOPLES_DEMOCRATIC_REPUBLIC = '120'
    LATVIA = '121'
    LEBANON = '122'
    LESOTHO = '123'
    LIBERIA = '124'
    LIBYAN_ARAB_JAMAHIRIYA = '125'
    LIECHTENSTEIN = '126'
    LITHUANIA = '127'
    LUXEMBOURG = '128'
    MACAO = '129'
    MACEDONIA = '130'
    MADAGASCAR = '131'
    MALAWI = '132'
    MALAYSIA = '133'
    MALDIVES = '134'
    MALI = '135'
    MALTA = '136'
    MARSHALL_ISLANDS = '137'
    MARTINIQUE = '138'
    MAURITANIA = '139'
    MAURITIUS = '140'
    MAYOTTE = '141'
    MEXICO = '142'
    MICRONESIA = '143'
    MOLDOVA = '144'
    MONACO = '145'
    MONGOLIA = '146'
    MONTSERRAT = '147'
    MOROCCO = '148'
    MOZAMBIQUE = '149'
    MYANMAR = '150'
    NAMIBIA = '151'
    NAURU = '152'
    NEPAL = '153'
    NETHERLANDS = '154'
    NETHERLANDS_ANTILLES = '155'
    NEW_CALEDONIA = '156'
    NEW_ZEALAND = '157'
    NICARAGUA = '158'
    NIGER = '159'
    NIGERIA = '160'
    NIUE = '161'
    NORFOLK_ISLAND = '162'
    NORTHERN_MARIANA_ISLANDS = '163'
    NORWAY = '164'
    OMAN = '165'
    PAKISTAN = '166'
    PALAU = '167'
    PALESTINIAN_TERRITORY = '168'
    PANAMA = '169'
    PAPUA_NEW_GUINEA = '170'
    PARAGUAY = '171'
    PERU = '172'
    PHILIPPINES = '173'
    PITCAIRN = '174'
    POLAND = '175'
    PORTUGAL = '176'
    PUERTO_RICO = '177'
    QATAR = '178'
    REUNION = '179'
    ROMANIA = '180'
    RUSSIAN_FEDERATION = '181'
    RWANDA = '182'
    SAINT_HELENA = '183'
    SAINT_KITTS_AND_NEVIS = '184'
    SAINT_LUCIA = '185'
    SAINT_PIERRE_AND_MIQUELON = '186'
    SAINT_VINCENT_AND_GRENADINES = '187'
    SAMOA = '188'
    SAN_MARINO = '189'
    SAO_TOME_AND_PRINCIPE = '190'
    SAUDI_ARABIA = '191'
    SENEGAL = '192'
    SERBIA_AND_MONTENEGRO = '193'
    SEYCHELLES = '194'
    SIERRA_LEONE = '195'
    SINGAPORE = '196'
    SLOVAKIA = '197'
    SLOVENIA = '198'
    SOLOMON_ISLANDS = '199'
    SOMALIA = '200'
    SOUTH_AFRICA = '201'
    SOUTH_GEORGIA_AND_SANDWICH_ISLANDS = '202'
    SPAIN = '203'
    SRI_LANKA = '204'
    SUDAN = '205'
    SURINAME = '206'
    SVALBARD_AND_JAN_MAYEN = '207'
    SWAZILAND = '208'
    SWEDEN = '209'
    SWITZERLAND = '210'
    SYRIAN_ARAB_REPUBLIC = '211'
    TAIWAN = '212'
    TAJIKISTAN = '213'
    TANZANIA = '214'
    THAILAND = '215'
    TIMOR_LESTE = '216'
    TOGO = '217'
    TOKELAU = '218'
    TONGA = '219'
    TRINIDAD_AND_TOBAGO = '220'
    TUNISIA = '221'
    TURKEY = '222'
    TURKMENISTAN = '223'
    TURKS_AND_CAICOS_ISLANDS = '224'
    TUVALU = '225'
    UGANDA = '226'
    UKRAINE = '227'
    UNITED_ARAB_EMIRATES = '228'
    UNITED_KINGDOM = '229'
    UNITED_STATES = '230'
    UNITED_STATES_MINOR_OUTLYING_ISLANDS = '231'
    URUGUAY = '232'
    UZBEKISTAN = '233'
    VANUATU = '234'
    VENEZUELA = '235'
    VIET_NAM = '236'
    VIRGIN_ISLANDS_BRITISH = '237'
    VIRGIN_ISLANDS_US = '238'
    WALLIS_AND_FUTUNA = '239'
    WESTERN_SAHARA = '240'
    YEMEN = '241'
    ZAMBIA = '242'
    ZIMBABWE = '243'

# Tax status codes and their allowed account types
TAX_STATUS_ACCOUNT_TYPES = {
    '01': ['SB', 'CB'],  # Individual
    '02': ['SB', 'CB'],  # On behalf of minor
    '03': ['SB', 'CB'],  # HUF
    '04': ['CB'],        # Company
    '05': ['CB'],        # AOP
    '06': ['CB'],        # Partnership Firm
    '07': ['CB'],        # Body Corporate
    '08': ['CB'],        # Trust
    '09': ['CB'],        # Society
    '10': ['CB'],        # Others
    '11': ['NE', 'NO'],  # NRI-Others
    '12': ['CB'],        # DFI
    '13': ['SB', 'CB'],  # Sole Proprietorship
    '21': ['NE'],        # NRE
    '22': ['CB'],        # OCB
    '23': ['NE', 'NO'],  # FII
    '24': ['NO'],        # NRO
    '25': ['NE', 'NO'],  # Overseas Corp. Body - Others
    '26': ['NE', 'NO'],  # NRI Child
    '27': ['NO'],        # NRI - HUF (NRO)
    '28': ['NO'],        # NRI - Minor (NRO)
    '29': ['NE'],        # NRI - HUF (NRE)
    '31': ['CB'],        # Provident Fund
    '32': ['CB'],        # Super Annuation Fund
    '33': ['CB'],        # Gratuity Fund
    '34': ['CB'],        # Pension Fund
    '36': ['CB'],        # Mutual Funds FOF Schemes
    '37': ['CB'],        # NPS Trust
    '38': ['NE', 'NO'],  # Global Development Network
    '39': ['NE', 'NO'],  # FCRA
    '41': ['NE', 'NO'],  # QFI - Individual
    '42': ['NE', 'NO'],  # QFI - Minors
    '43': ['CB'],        # QFI - Corporate
    '44': ['CB'],        # QFI - Pension Funds
    '45': ['CB'],        # QFI - Hedge Funds
    '46': ['CB'],        # QFI - Mutual Funds
    '47': ['CB'],        # LLP
    '48': ['CB'],        # Non-Profit organization [NPO]
    '51': ['CB'],        # Public Limited Company
    '52': ['CB'],        # Private Limited Company
    '53': ['CB'],        # Unlisted Company
    '54': ['CB'],        # Mutual Funds
    '55': ['NE', 'NO'],  # FPI - Category I
    '56': ['NE', 'NO'],  # FPI - Category II
    '57': ['NE', 'NO'],  # FPI - Category III
    '58': ['CB'],        # Financial Institutions
    '59': ['CB'],        # Body of Individuals
    '60': ['CB'],        # Insurance Company
    '61': ['NE'],        # OCI - Repatriation
    '62': ['NO'],        # OCI - Non Repatriation
    '70': ['NE', 'NO'],  # Person of Indian Origin
    '72': ['CB'],        # Government Body
    '73': ['CB'],        # Defense Establishment
    '74': ['CB'],        # Non - Government Organisation
    '75': ['CB'],        # Bank/Co-Operative Bank
    '76': ['NE'],        # Seafarer NRE
    '77': ['NO'],        # Seafarer NRO
}

class ClientRegistration(BaseModel):
    # Basic Client Information
    ClientCode: constr(min_length=1, max_length=10)
    PrimaryHolderFirstName: constr(min_length=1, max_length=70)
    PrimaryHolderMiddleName: Optional[constr(max_length=70)] = None
    PrimaryHolderLastName: Optional[constr(max_length=70)] = None
    TaxStatus: constr(min_length=2, max_length=2, regex='^[0-9]{2}$')
    Gender: Gender
    PrimaryHolderDOB: str
    OccupationCode: OccupationCode
    HoldingNature: HoldingNature
    DividendPayMode: DividendPayMode

    # Secondary Holder Details
    SecondHolderFirstName: Optional[constr(max_length=70)] = None
    SecondHolderMiddleName: Optional[constr(max_length=70)] = None
    SecondHolderLastName: Optional[constr(max_length=70)] = None
    SecondHolderDOB: Optional[str] = None

    # Third Holder Details
    ThirdHolderFirstName: Optional[constr(max_length=70)] = None
    ThirdHolderMiddleName: Optional[constr(max_length=70)] = None
    ThirdHolderLastName: Optional[constr(max_length=70)] = None
    ThirdHolderDOB: Optional[str] = None

    # Guardian Details
    GuardianFirstName: Optional[constr(max_length=70)] = None
    GuardianMiddleName: Optional[constr(max_length=70)] = None
    GuardianLastName: Optional[constr(max_length=70)] = None
    GuardianDOB: Optional[str] = None

    # PAN Details
    PrimaryHolderPANExempt: constr(regex='^[YN]$')
    SecondHolderPANExempt: Optional[constr(regex='^[YN]$')] = None
    ThirdHolderPANExempt: Optional[constr(regex='^[YN]$')] = None
    GuardianPANExempt: Optional[constr(regex='^[YN]$')] = None
    PrimaryHolderPAN: Optional[constr(regex='^[A-Z]{5}[0-9]{4}[A-Z]$')] = None
    SecondHolderPAN: Optional[constr(regex='^[A-Z]{5}[0-9]{4}[A-Z]$')] = None
    ThirdHolderPAN: Optional[constr(regex='^[A-Z]{5}[0-9]{4}[A-Z]$')] = None
    GuardianPAN: Optional[constr(regex='^[A-Z]{5}[0-9]{4}[A-Z]$')] = None

    # Exempt Categories
    PrimaryHolderExemptCategory: Optional[PANExemptCategory] = None
    SecondHolderExemptCategory: Optional[PANExemptCategory] = None
    ThirdHolderExemptCategory: Optional[PANExemptCategory] = None
    GuardianExemptCategory: Optional[PANExemptCategory] = None

    # Client Type and Account Details
    ClientType: constr(min_length=1, max_length=2)
    PMS: Optional[constr(regex='^[YN]$')] = None
    DefaultDP: constr(regex='^[NC]$')

    # Demat Account Details
    CDSLDPID: Optional[constr(max_length=16)] = None
    CDSLCLTID: Optional[constr(max_length=16)] = None
    CMBPId: Optional[constr(max_length=8)] = None
    NSDLDPID: Optional[constr(max_length=8)] = None
    NSDLCLTID: Optional[constr(max_length=8)] = None

    # Bank Account Details
    AccountType1: AccountType
    AccountNo1: constr(min_length=1, max_length=20)
    MICRNo1: constr(regex='^[0-9]{9}$')
    IFSCCode1: constr(regex='^[A-Z]{4}0[A-Z0-9]{6}$')
    DefaultBankFlag1: constr(regex='^[YN]$')

    # Contact Information
    Address1: constr(min_length=1, max_length=40)
    Address2: Optional[constr(max_length=40)] = None
    Address3: Optional[constr(max_length=40)] = None
    City: constr(min_length=1, max_length=35)
    State: StateCode
    Pincode: constr(regex='^[0-9]{6}$')
    Country: CountryCode
    ResiPhone: Optional[constr(regex='^\+?[0-9]{10,15}$')] = None
    ResiFax: Optional[constr(regex='^\+?[0-9]{10,15}$')] = None
    OfficePhone: Optional[constr(regex='^\+?[0-9]{10,15}$')] = None
    OfficeFax: Optional[constr(regex='^\+?[0-9]{10,15}$')] = None
    Email: EmailStr
    CommunicationMode: CommunicationMode

    # Additional Fields
    AadhaarUpdated: Optional[constr(regex='^[YN]$')] = None
    MapinId: Optional[constr(max_length=10)] = None
    PaperlessFlag: Optional[constr(regex='^[YN]$')] = None
    LEINo: Optional[constr(max_length=20)] = None
    LEIValidity: Optional[str] = None
    MobileDeclarationFlag: constr(regex='^[YN]$')
    EmailDeclarationFlag: constr(regex='^[YN]$')

    @validator('*')
    def validate_empty_strings(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @validator('PrimaryHolderDOB', 'SecondHolderDOB', 'ThirdHolderDOB', 'GuardianDOB', 'LEIValidity')
    def validate_date_format(cls, v):
        if v:
            try:
                day, month, year = map(int, v.split('/'))
                date(year, month, day)
                return v
            except (ValueError, TypeError):
                raise ValueError('Invalid date format. Use DD/MM/YYYY')
        return v

    @validator('AccountType1')
    def validate_account_type_for_tax_status(cls, v, values):
        tax_status = values.get('TaxStatus')
        if tax_status:
            allowed_types = TAX_STATUS_ACCOUNT_TYPES.get(tax_status, [])
            if v not in allowed_types:
                raise ValueError(f'Invalid account type {v} for tax status {tax_status}. Allowed types: {", ".join(allowed_types)}')
        return v

    @validator('PrimaryHolderPAN')
    def validate_primary_pan(cls, v, values):
        if values.get('PrimaryHolderPANExempt') == 'N' and not v:
            raise ValueError('PAN is required when not exempt')
        return v

    @validator('PrimaryHolderExemptCategory')
    def validate_pan_exempt_category(cls, v, values):
        if values.get('PrimaryHolderPANExempt') == 'Y' and not v:
            raise ValueError('PAN exempt category is required when PAN is exempt')
        return v

    @validator('CDSLDPID', 'CDSLCLTID')
    def validate_cdsl_fields(cls, v, values):
        if values.get('DefaultDP') == 'C' and not v:
            raise ValueError('Required when DefaultDP is CDSL')
        return v

    @validator('NSDLDPID', 'NSDLCLTID')
    def validate_nsdl_fields(cls, v, values):
        if values.get('DefaultDP') == 'N' and not v:
            raise ValueError('Required when DefaultDP is NSDL')
        return v

    @validator('GuardianFirstName', 'GuardianLastName', 'GuardianDOB')
    def validate_guardian_details(cls, v, values):
        dob = values.get('PrimaryHolderDOB')
        if dob:
            try:
                day, month, year = map(int, dob.split('/'))
                holder_dob = date(year, month, day)
                today = date.today()
                age = today.year - holder_dob.year - ((today.month, today.day) < (holder_dob.month, holder_dob.day))
                if age < 18 and not v:
                    raise ValueError('Guardian details required for minor account holder')
            except (ValueError, TypeError):
                pass
        return v

    @validator('SecondHolderFirstName', 'SecondHolderLastName')
    def validate_second_holder(cls, v, values):
        if values.get('HoldingNature') in ['JO', 'AS'] and not v:
            raise ValueError('Second holder details required for Joint/Anyone or Survivor holding')
        return v

    class Config:
        anystr_strip_whitespace = True
        extra = 'forbid'  # Forbid extra fields
        validate_assignment = True  # Validate when values are assigned
        error_msg_templates = {
            'type_error': 'Invalid type for {field_name}',
            'value_error.missing': '{field_name} is required',
            'value_error.any_str.max_length': '{field_name} must be at most {limit_value} characters',
            'value_error.str.regex': 'Invalid format for {field_name}'
        } 
