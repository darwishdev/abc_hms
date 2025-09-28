erpnext.selling.POSInvoiceController = class POSInvoiceController extends (
    erpnext.selling.SellingController
) {
    change_amount() {
        this.frm.set_value("change_amount", 0.0);
        this.frm.set_value("base_change_amount", 0.0);
        this.frm.refresh_fields();
    }
};
