
from erpnext.accounts.doctype.pos_invoice.pos_invoice import SalesInvoice
from frappe.utils import  cint
from erpnext.accounts.utils import (
	get_account_currency,
)
class CustomSalesInvoice(SalesInvoice):
	def make_pos_gl_entries(self, gl_entries):
		if cint(self.is_pos):
			for payment_mode in self.payments:
				against_voucher = self.name
				if self.is_return and self.return_against and not self.update_outstanding_for_self:
					against_voucher = self.return_against

				if payment_mode.base_amount:
					# POS, make payment entries
					gl_entries.append(
						self.get_gl_dict(
							{
								"account": self.debit_to,
								"party_type": "Customer",
								"party": self.customer,
								"against": payment_mode.account,
								"credit": payment_mode.base_amount,
								"credit_in_account_currency": payment_mode.base_amount
								if self.party_account_currency == self.company_currency
								else payment_mode.amount,
								"credit_in_transaction_currency": payment_mode.amount,
								"against_voucher": against_voucher,
								"against_voucher_type": self.doctype,
								"cost_center": self.cost_center,
							},
							self.party_account_currency,
							item=self,
						)
					)

					payment_mode_account_currency = get_account_currency(payment_mode.account)
					gl_entries.append(
						self.get_gl_dict(
							{
								"account": payment_mode.account,
								"against": self.customer,
								"debit": payment_mode.base_amount,
								"debit_in_account_currency": payment_mode.base_amount
								if payment_mode_account_currency == self.company_currency
								else payment_mode.amount,
								"debit_in_transaction_currency": payment_mode.amount,
								"cost_center": self.cost_center,
							},
							payment_mode_account_currency,
							item=self,
						)
					)


