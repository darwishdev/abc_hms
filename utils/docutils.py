from typing import TypeVar, Type, cast
import frappe
from frappe.model.document import Document

T = TypeVar('T', bound=Document)

def get_doc_typed(doctype: str, name: str, doc_class: Type[T]) -> T:
    """Generic function to get a document with proper typing"""
    return cast(T, frappe.get_doc(doctype, name))
