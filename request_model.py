from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum

class State(str, Enum):
    AL = 'Alabama'
    AK = 'Alaska'
    AZ = 'Arizona'
    AR = 'Arkansas'
    CA = 'California'
    CO = 'Colorado'
    CT = 'Connecticut'
    DE = 'Delaware'
    FL = 'Florida'
    GA = 'Georgia'
    HI = 'Hawaii'
    ID = 'Idaho'
    IL = 'Illinois'
    IN = 'Indiana'
    IA = 'Iowa'
    KS = 'Kansas'
    KY = 'Kentucky'
    LA = 'Louisiana'
    ME = 'Maine'
    MD = 'Maryland'
    MA = 'Massachusetts'
    MI = 'Michigan'
    MN = 'Minnesota'
    MS = 'Mississippi'
    MO = 'Missouri'
    MT = 'Montana'
    NE = 'Nebraska'
    NV = 'Nevada'
    NH = 'New Hampshire'
    NJ = 'New Jersey'
    NM = 'New Mexico'
    NY = 'New York'
    NC = 'North Carolina'
    ND = 'North Dakota'
    OH = 'Ohio'
    OK = 'Oklahoma'
    OR = 'Oregon'
    PA = 'Pennsylvania'
    RI = 'Rhode Island'
    SC = 'South Carolina'
    SD = 'South Dakota'
    TN = 'Tennessee'
    TX = 'Texas'
    UT = 'Utah'
    VT = 'Vermont'
    VA = 'Virginia'
    WA = 'Washington'
    WV = 'West Virginia'
    WI = 'Wisconsin'
    WY = 'Wyoming'
    DC = 'Washington, D.C.'

    # @classmethod
    # def get_abbreviation(cls, full_name: str):
    #     # Create a lookup dictionary from Enum
    #     state_map = {state.value: state.name for state in cls}
    #     return state_map.get(full_name)


class NamlEligible(str, Enum):
    Y = "Yes"
    N = "No"
    U = "Unclear"

class Coverage(str, Enum):
    D="D"
    E="E"
    F="F"

class Broker(BaseModel):
    name:str
    organization:str
    address:str
    city:str
    state:State
    zipcode:str = Field(..., max_length=5) #, regex=r'^\d{5}$'
    delegate:str


class Applicant(BaseModel):
    # applicant_id:Optional[str]
    name:str
    address:str
    city:str
    state:State
    zipcode:str = Field(..., max_length=5) #, regex=r'^\d{5}$'
    naics:str = Field(..., min_length=6, max_length=6)


class Financial(BaseModel):
    NAML_eligible: NamlEligible
    employee_count:int = Field(..., gt=0)
    revenue:int #Optional[int]
    current_assets:int
    current_liabilities:int
    total_assets:int
    total_liabilities:int
    net_income_loss:int

    coverage:List[Coverage] ## Optional[List[Coverage]]
    retained_earning:Optional[int]
    end_ebit:Optional[int]
    total_claims:Optional[int]


# Main Payload Model
class RequestPayload(BaseModel):
    broker: Broker
    applicant: Applicant
    financial: Financial
