frappe.after_ajax(() => {
    setTimeout(() => {
        const $navbar = $("#navbar-search");
        if ($navbar.length && !$navbar.find(".business-date-item").length) {
            $navbar.append(`
                    <li class="nav-item business-date-item">
                        <a class="nav-link" href="#">
                            📅 ${frappe.boot.business_date}
                        </a>
                    </li>
                `);
        }
    }, 5000);
});
