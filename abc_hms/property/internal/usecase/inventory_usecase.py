from typing import Dict

from utils.date_utils import date_to_int
from ..repo.inventory_repo import InventoryRepo

class InventoryUsecase:
    def __init__(self) -> None:
        self.repo = InventoryRepo()
    def room_date_lookup_list(self , lookup_type: list[str] | None = None):
        data = self.repo.room_date_lookup_list(lookup_type)
        result = {}
        for row in data:
            lt = row["lookup_type"]
            if lt not in result:
                result[lt] = {}
            result[lt][row["lookup_key"]] = row["lookup_value"]
        return result

    def to_int(self , value: str | None):
        if value is None or value == "" or value == "None":
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    def inventory_upsert(self, params: Dict):
        args = (
                params.get("room"),
                params.get("user"),
                date_to_int(params.get("date_range")[0]),
                date_to_int(params.get("date_range")[1]),
                self.to_int(params.get("physical_status")),
                self.to_int(params.get("room_status")),
                self.to_int(params.get("hk_status")),
                self.to_int(params.get("service_status")),
                self.to_int(params.get("ooo_status")),
                params.get("reason"),
            )
        return self.repo.inventory_upsert(args)


    def normalize_status(self ,value: str, status_map: dict):
        """Convert string to mapped int, default to 0 if None/empty/unmapped."""
        if not value:  # None or empty string
            return 0
        return status_map.get(value, 0)
    def room_status_list(self, params: Dict):
        date_from, date_to = params.get("date_range", [None, None])
        guest_status_map = {
            "Do Not Disturb": 1,
            "Make Up Room": 2,
        }

        room_status_map = {
            "Vacant": 1,
            "Occupied": 2,
        }

        hk_status_map = {
            "Clean": 0,
            "Inspected": 1,
            "Dirty": 2,
        }

        def clean_empty_string(value):
            """Convert empty strings to None"""
            return None if value == "" else value
        prepared = {
            "room": params.get("room"),
            "room_status": params.get("room_status"),
            "property": clean_empty_string(params.get("property")),
            "hk_section": clean_empty_string(params.get("hk_section")),
            "room_status": clean_empty_string(params.get("room_status")),
            "room_category": clean_empty_string(params.get("room_category")),
            "room_type": clean_empty_string(params.get("room_type")),
            "room_status_map": self.normalize_status(params.get("room_status_map"), room_status_map),
            "hk_status": self.normalize_status(params.get("hk_status"), hk_status_map),
            "guest_service_status": self.normalize_status(
                params.get("guest_service_status"), guest_status_map
            ),
            "date_from": date_to_int(date_from),
            "date_to": date_to_int(date_to),
        }
        return self.repo.room_status_list(prepared)
