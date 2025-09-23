from typing import Dict, List, Union
import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.property_room_date_dto import RoomDateBulkUpsertRequest, RoomDateBulkUpsertResponse

@frappe.whitelist(methods=["POST", "PUT"])
def room_date_bulk_upsert(room_numbers , for_date,updated_fields):
    if isinstance(room_numbers, str):
        try:
            parsed_room_numbers: List[str] = json.loads(room_numbers)
        except json.JSONDecodeError:
            parsed_room_numbers = [room_numbers]
    else:
        parsed_room_numbers: List[str] = list(room_numbers)

    parsed_for_date: int = int(for_date)

    # updated_fields → Dict[str, number]
    if isinstance(updated_fields, str):
        try:
            parsed_updated_fields: Dict[str, Union[int, float]] = json.loads(updated_fields)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid updated_fields: {updated_fields}")
    else:
        parsed_updated_fields: Dict[str, Union[int, float]] = dict(updated_fields)

    return app_container.room_date_usecase.room_date_bulk_upsert(parsed_room_numbers,parsed_for_date,parsed_updated_fields ,True)
