from frappe.utils import getdate
from datetime import date

def date_to_int(d) -> int:
    """Convert date/datetime to int YYYYMMDD."""
    d = getdate(d)
    return int(d.strftime("%Y%m%d"))

def int_to_date(n: int) -> date:
    """Convert int YYYYMMDD to date."""
    s = str(n)
    return getdate(f"{s[:4]}-{s[4:6]}-{s[6:]}")
