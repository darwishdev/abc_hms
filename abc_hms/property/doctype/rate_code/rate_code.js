// Copyright (c) 2025, Your Name and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rate Code", {
    refresh(frm) {
        frm.set_query("currency", () => {
            return {
                query: "abc_hms.currency_list_input", // path to your Python function
            };
        });
    },
});
