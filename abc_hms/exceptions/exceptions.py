# abc_hms/abc_hms/exceptions.py

import json
from frappe import ValidationError


class EndOfDayValidationError(ValidationError):
    def __init__(self, message, data=None):
        payload = {
            "message": message,
            "data": data or {}
        }
        super().__init__(json.dumps(payload))

