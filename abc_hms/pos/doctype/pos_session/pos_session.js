frappe.ui.form.on("POS Session", {
    property: function (frm) {
        if (!frm.doc.property) return;
        frm.call("get_defaults").then((r) => {
            if (r.message && r.message.success && r.message.doc) {
                const defaults = r.message.doc;
                frm.set_value("pos_profile", defaults.pos_profile);
                frm.set_value("for_date", defaults.for_date);
                frm.set_value("opening_entry", defaults.opening_entry || "");
            }
        });
    },
});
