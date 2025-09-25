frappe.ui.form.on("POS Session", {
    pos_profile: function (frm) {
        if (!frm.doc.pos_profile) return;
        frm.call("get_current_bussiness_date").then((r) => {
            console.log("bznsss datea fetchecd");
        });
    },
});
