frappe.after_ajax(() => {
    console.log("calledddd");
    setTimeout(() => {
        frappe.call({
            method: "abc_hms.default_property_setting_find",
            type: "GET",
            //args: { property_name: "CHNA" },
            callback: ({ message }) => {
                // Use 'callback' instead of 'success' for better practice
                const record = Array.isArray(message) ? message[0] : message?.data?.[0] || message;

                if (!record) return;

                const propertyName = record.property_name || record.name || "Property";
                const businessDate = record.business_date || "";
                console.log("response isss", message);
                console.log("message", message);
                const $navbar = $("body");
                if ($navbar.length && !$navbar.find("#top-nav").length) {
                    $navbar.prepend(`
                        <div id="top-nav" class="top-nav">
                            <h4><span class="fa fa-calendar mr-2"></span>${propertyName} : ${businessDate}</h4>
                            <ul>
                                <li><a href="https://www.facebook.com/" target="_blank"><span class="fa fa-facebook-square"></span> </a></li>
                                <li><a href="https://www.linkedin.com/company/abc-hotels-group" target="_blank"><span class="fa fa-linkedin-square"></span></a></li>
                                <li><a href="https://www.instagram.com/" target="_blank"><span class="fa fa-instagram"></span> </a></li>
                            </ul>
                        </div>
                    `);
                }
            },
        });
    }, 500);
});
