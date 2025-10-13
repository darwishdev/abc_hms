frappe.ui.form.on("Folio", {
    refresh(frm) {
        // Clear any existing custom buttons
        frm.clear_custom_buttons();
        frm.add_custom_button("Merge Folio", () => {
            const d = new frappe.ui.Dialog({
                title: "Merge Folio",
                fields: [
                    {
                        fieldname: "destination_folio",
                        label: "Destination Folio",
                        fieldtype: "Link",
                        options: "Folio",
                        reqd: 1,
                        get_query() {
                            return {
                                filters: [
                                    ["name", "!=", frm.doc.name], // exclude current folio
                                ],
                            };
                        },
                        onchange: function () {
                            const dest_folio = d.get_value("destination_folio");
                            if (dest_folio) {
                                d.set_df_property("destination_window", "read_only", 0);
                                d.set_value("destination_window", null);
                            } else {
                                d.set_df_property("destination_window", "read_only", 1);
                                d.set_value("destination_window", null);
                            }
                        },
                    },
                    {
                        fieldname: "destination_window",
                        label: "Destination Window",
                        fieldtype: "Link",
                        options: "Folio Window",
                        reqd: 1,
                        read_only: 1,
                        get_query() {
                            const dest_folio = d.get_value("destination_folio");
                            return {
                                filters: dest_folio ? { folio: dest_folio } : {},
                            };
                        },
                    },
                ],
                primary_action_label: "Merge",
                primary_action(values) {
                    if (!values.destination_folio || !values.destination_window) {
                        frappe.msgprint("Please select both destination folio and window.");
                        return;
                    }

                    frm.call("folio_merge", {
                        destination_folio: values.destination_folio,
                        destination_window: values.destination_window,
                    }).then((res) => {
                        frappe.show_alert({
                            message: __("Folio merged successfully"),
                            indicator: "green",
                        });
                        d.hide();
                        frm.reload_doc();
                    });
                },
            });

            d.show();
        });
        if (frm.doc.folio_status === "Settled") {
            frm.add_custom_button("Submit Folio", () => {
                frm.call("folio_submit");
            });
            return;
        }
        // --- Make Payment Button ---
        frm.add_custom_button("Make Payment", () => {
            frappe.call({
                method: "abc_hms.porfile_mode_of_payment_list",
                type: "GET",
                headers: {
                    "X-Pos-Profile": "Main", // or dynamically frm.doc.pos_profile
                },
                callback: function (r) {
                    if (r.message) {
                        // Convert [{name: "Cash"}, ...] → ["Cash", ...]
                        const payment_modes = r.message.map((item) => item.name);

                        const d = new frappe.ui.Dialog({
                            title: "Make Payment",
                            fields: [
                                {
                                    fieldname: "mode_of_payment",
                                    label: "Mode of Payment",
                                    fieldtype: "Select",
                                    options: payment_modes,
                                    reqd: 1,
                                },
                                {
                                    fieldname: "folio_window",
                                    label: "Folio Window",
                                    fieldtype: "Link",
                                    options: "Folio Window",
                                    get_query() {
                                        return {
                                            filters: {
                                                folio: frm.doc.name, // filter by current folio
                                            },
                                        };
                                    },
                                    onchange: function () {
                                        const folio_window = d.get_value("folio_window");
                                        if (folio_window) {
                                            // Call a frappe method to get the remaining balance
                                            frm.call("folio_find_balance", {
                                                window: folio_window,
                                            }).then((res) => {
                                                if (res.message) {
                                                    const { amount, paid } = res.message.balance;
                                                    const balance = amount - paid;
                                                    d.set_value("amount", balance || 0);
                                                }
                                            });
                                        }
                                    },
                                },
                                {
                                    fieldname: "amount",
                                    label: "Amount",
                                    fieldtype: "Currency",
                                    reqd: 1,
                                },
                            ],
                            primary_action_label: "Submit Payment",
                            primary_action(values) {
                                frm.call("make_payment", {
                                    mode_of_payment: values.mode_of_payment,
                                    amount: values.amount,
                                    window: values.folio_window,
                                }).then(() => {
                                    frappe.msgprint("Payment submitted successfully");
                                    d.hide();
                                    frm.reload_doc();
                                });
                            },
                        });

                        d.show();
                    }
                },
            });
        });

        // --- Submit Button (only if Settled) ---
        if (frm.doc.status === "Settled") {
            frm.add_custom_button("Submit", () => {
                frappe.call({
                    method: "abc_hms.api.submit_folio",
                    args: { folio: frm.doc.name },
                    callback(res) {
                        if (!res.exc) {
                            frappe.msgprint("Folio submitted successfully");
                            frm.reload_doc();
                        }
                    },
                });
            });
        }
    },
});
