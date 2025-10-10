# abc_hms/abc_hms/exceptions.py

import json
from frappe import ValidationError
class AvailabilityError(ValidationError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class RoomShareError(ValidationError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class EndOfDayValidationError(ValidationError):
    def __init__(self, message, data=None):
        payload = {
            "message": message,
            "data": data or {}
        }
        super().__init__(json.dumps(payload))

