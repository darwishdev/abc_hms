import frappe
from frappe import _
from typing import Dict
from frappe.core.doctype.user.user import User
from utils.docutils import get_doc_typed
from ..repo.auth_repo import AuthRepo
from frappe.utils.password import get_decrypted_password

class AuthUsecase:
    def __init__(self, repo: AuthRepo) -> None:
        self.repo = repo

    def generate_keys(self , user: str):
        user_details = get_doc_typed("User", user, User)
        if user_details.api_key:
            try:
                api_secret = get_decrypted_password("User", user, "api_secret")
            except:
                api_secret = None
            return {"api_key": user_details.api_key, "api_secret":  api_secret}
        api_secret = frappe.generate_hash(length=15)
        # if api key is not set generate api key
        if not user_details.api_key:
            api_key = frappe.generate_hash(length=15)
            user_details.api_key = api_key

        user_details.api_secret = api_secret
        user_details.save(ignore_permissions=True)
        return {"api_key": user_details.api_key, "api_secret": api_secret}

    def cashier_login(self, code: int, password: str) -> Dict:
        user_name = self.repo.user_find_by_cashier_code(str(code), password)
        if not user_name or user_name is None:
            frappe.throw(_("User Not Found"))

        keys_result = self.generate_keys(user_name)
        api_key = keys_result.get("api_key")
        api_secret = keys_result.get("api_secret")

        token_value = f"{api_key}:{api_secret}"
        return {
            "success": True,
            "authorization": token_value,
            "token_type": "token",
            "user": user_name,
            "username": user_name,
            "message": "Login successful"
        }
