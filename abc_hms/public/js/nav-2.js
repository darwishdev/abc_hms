frappe.after_ajax(() => {
    setTimeout(() => {
        console.log("appender nave");
        const $navbar = $("body");
        if ($navbar.length && !$navbar.find("#to-nav").length) {
            $navbar.prepend(`
                <div id"top-nav" class="top-nav">
                    <h4><span class="fa fa-calendar mr-2"></span>${__("Business Date")} : ${frappe.boot.business_date}</h4>
                    <ul>
 <li><a href="https://www.facebook.com/" target="_blank"><span class="fa fa-facebook-square"></span> </a></li>
                        <li><a href="https://www.linkedin.com/company/abc-hotels-group" target="_blank"><span class="fa fa-linkedin-square"></span></a></li>
                        <li><a href="https://www.instagram.com/" target="_blank"><span class="fa fa-instagram"></span> </a></li>
                    </ul>
                </div>
                `);
        }
    }, 500);
});
