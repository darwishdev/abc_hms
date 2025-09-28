from decimal import Decimal
from typing import List, TypedDict, Union

from frappe import Optional
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from erpnext.accounts.doctype.pos_invoice_item.pos_invoice_item import POSInvoiceItem

class ItemListRequest(TypedDict):
    pos_profile: str
