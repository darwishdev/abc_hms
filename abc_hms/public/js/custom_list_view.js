frappe.provide("frappe.views");

class CustomListView extends frappe.views.ListView {
    make_sidebar() {
        super.make_sidebar();

        // Add your persistent sidebar content
        this.sidebar.append(`
            <div class="my-global-sidebar">
                <h5>📌 Hotels Sidebar</h5>
                <ul>
                    <li><a href="/app/hotel-reservation">Reservations</a></li>
                    <li><a href="/app/folio">Folios</a></li>
                    <li><a href="/app/room">Rooms</a></li>
                </ul>
            </div>
        `);
    }

    render() {
        // Optionally extend the whole render cycle
        super.render();
    }
}

// Override the global ListView class
frappe.views.ListView = CustomListView;
