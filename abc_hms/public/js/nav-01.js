frappe.after_ajax(() => {
    setTimeout(() => {
        const property = frappe.defaults.get_user_default("Property");
        console.log("property is ", property);
        if (!property) {
            console.warn("No Property default set for this user.");
            return;
        }
        frappe.db
            .get_value("Property Setting", { property: property }, "business_date")
            .then((r) => {
                if (!r || !r.message) return;
                const business_date = r.message.business_date;
                const $navbar = $("#navbar-breadcrumbs");
                if ($navbar.length && !$navbar.find(".business-date-item").length) {
                    $navbar.append(`
                    <li class="nav-item business-date-item">
                        <a class="nav-link" href="#">
                            📅 ${business_date}
                        </a>
                    </li>
                `);
                }
            });
    }, 500);
});
