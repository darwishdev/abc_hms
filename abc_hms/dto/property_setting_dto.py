
from typing import TypedDict, Union
from frappe import Optional

from abc_hms.dto.dto_helpers import ErrorResponse

from abc_hms.property.doctype.property_setting.property_setting import PropertySetting


class PropertySettingUpsertRequest(TypedDict):
    """API request DTO"""
    doc: PropertySetting
    commit: bool

class PropertySettingUpsertResult(TypedDict):
    """API response DTO"""
    success: bool
    doc: PropertySetting

PropertySettingUpsertResponse = Union[PropertySettingUpsertResult, ErrorResponse]

class PropertySettingBusinessDateFindRequest(TypedDict):
    """API request DTO - find business date for a property"""
    property_name: str

class PropertySettingBusinessDateFindResult(TypedDict):
    """API response DTO"""
    company_name: str
    default_pos_profile: str
    default_rooms_item_group: str
    business_date_str: str
    business_date_int: int


PropertySettingBusinessDateFindResponse = Union[PropertySettingBusinessDateFindResult, ErrorResponse]
class PropertySettingIncreaseBusinessDateFindRequest(TypedDict):
    """API request DTO - increase business date for a property"""
    property_name: str
    commit: Optional[bool]


class PropertySettingIncreaseBusinessDateFindResult(TypedDict):
    """API response DTO"""
    success: bool
    doc: PropertySetting


PropertySettingIncreaseBusinessDateFindResponse = Union[PropertySettingIncreaseBusinessDateFindResult, ErrorResponse]

class PropertySettingFindRequest(TypedDict):
    property_name: str


class PropertySettingData(PropertySetting):
    default_pos_profile: str
    business_date: str
    business_date_int: int
    company: str

class PropertySettingFindResult(TypedDict):
    success: bool
    doc: PropertySettingData


PropertySettingFindResponse = Union[PropertySettingFindResult, ErrorResponse]

