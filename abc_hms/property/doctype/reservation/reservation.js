frappe.ui.form.on("Reservation", {
    refresh(frm) {
        //
        // Check for availability errors after any server call
        if (
            frappe.last_response &&
            frappe.last_response.availability_error &&
            frappe.last_response.availability_error.has_error
        ) {
            let error_data = frappe.last_response.availability_error;

            frappe.msgprint({
                message: `Error Syncing the reservation: ${error_data.error_message}`,
                title: "Sync Error",
                indicator: "red",
                primary_action: {
                    label: "Ignore",
                    action: function () {
                        console.log("ignoring");
                        cur_dialog.hide();

                        // Apply workflow with ignore
                        frappe.call({
                            method: "frappe.model.workflow.apply_workflow",
                            args: {
                                doc: frm.doc,
                                action: error_data.action,
                                ignore_availability: 1, // This should be handled in your workflow
                            },
                            callback: function () {
                                frm.reload_doc();
                            },
                        });
                    },
                },
            });

            // Clear the error
            delete frappe.last_response.availability_error;
        }
        handle_availability_button(frm);
    },
    property(frm) {
        handle_availability_button(frm);
    },
    validate(frm) {
        validate_reservation(frm);
    },
    arrival(frm) {
        validate_arrival(frm);
        sync_departure_from_arrival(frm);
        handle_availability_button(frm);
    },
    departure(frm) {
        validate_departure(frm);
        sync_nights_from_departure(frm);
        handle_availability_button(frm);
    },
    base_rate(frm) {
        console.log("frm", frm.is_dirty(), frm.is_new());
        const selected = frm.selected_rate;
        if (!selected) return;

        const current = parseFloat(frm.doc.base_rate || 0);
        if (current !== selected.base_rate) {
            frm.set_value("fixed_rate", 1);
        } else {
            frm.set_value("fixed_rate", 0);
        }
    },
    nights(frm) {
        validate_nights(frm);
        sync_departure_from_nights(frm);
        handle_availability_button(frm);
    },
    number_of_rooms(frm) {
        validate_number_of_rooms(frm);
    },
});

const handle_availability_button = (frm) => {
    const can_show =
        frm.doc.property &&
        frm.doc.docstatus === 0 &&
        frm.doc.arrival &&
        frm.doc.departure &&
        frm.doc.nights > 0;

    if (!can_show || !frm.is_dirty()) {
        frm.remove_custom_button("Get Availability");
        return;
    }

    frm.add_custom_button(__("Get Availability"), async () => {
        await reservation_availability_check(frm);
    });
};

const show_availability = (wrapper, html) => {
    wrapper.html(html).closest(".form-group").toggle(true);
};

const get_availability_wrapper = (frm) => {
    if (frm.fields_dict.availability_html) return $();
    return $(frm.dashboard.wrapper);
};

const reservation_availability_check = async (frm) => {
    const wrapper = frm.fields_dict.availability_html.$wrapper;
    if (!wrapper) return console.error("Availability HTML Input not found");
    frm.call("get_availability")
        .then((result) => {
            if (result.message) {
                show_availability(wrapper, result.message);
                wrapper.data("frm", frm);
            }
        })
        .catch((err) => {
            show_availability(
                wrapper,
                `<div class="alert alert-danger">Error: ${err.message}</div>`,
            );
        });
};

const validate_reservation = (frm) => {
    validate_arrival(frm);
    validate_departure(frm);
    validate_nights(frm);
    validate_number_of_rooms(frm);
    validate_consistency(frm);
};

const validate_arrival = (frm) => {
    const { arrival } = frm.doc;
    const business_date = frappe.boot.business_date;

    if (arrival && arrival < business_date) {
        frappe.throw(__(`Arrival date cannot be before business date (${business_date}).`));
    }
};

const validate_departure = (frm) => {
    const { arrival, departure } = frm.doc;
    if (arrival && departure && departure <= arrival) {
        frappe.throw(__("Departure date must be after arrival date."));
    }
};

const validate_nights = (frm) => {
    const { nights } = frm.doc;
    if (nights && nights <= 0) {
        frappe.throw(__("Number of nights must be at least 1."));
    }
};

const validate_number_of_rooms = (frm) => {
    const { number_of_rooms } = frm.doc;
    if (!number_of_rooms || number_of_rooms < 1) {
        frappe.throw(__("At least one room must be reserved."));
    }
};

const validate_consistency = (frm) => {
    const { arrival, departure, nights } = frm.doc;
    if (arrival && departure && nights) {
        const diff = frappe.datetime.get_diff(departure, arrival); // in days
        if (diff !== nights) {
            frappe.throw(
                __("Nights must equal the difference between departure and arrival dates."),
            );
        }
    }
};

const sync_departure_from_arrival = (frm) => {
    const { arrival, nights } = frm.doc;
    if (arrival && nights) {
        frm.set_value("departure", frappe.datetime.add_days(arrival, nights));
    }
};

const sync_nights_from_departure = (frm) => {
    const { arrival, departure } = frm.doc;
    if (arrival && departure) {
        frm.set_value("nights", frappe.datetime.get_diff(departure, arrival));
    }
};

const sync_departure_from_nights = (frm) => {
    const { arrival, nights } = frm.doc;
    if (arrival && nights) {
        frm.set_value("departure", frappe.datetime.add_days(arrival, nights));
    }
};

window.ignore_availability_action = function () {
    frappe.call({
        method: "abc_hms.reservation_sync_days",
        args: {
            doc: cur_frm.doc,
            ignore_availability: 1,
        },
        callback: function (r) {
            frappe.show_alert({ message: "Availability ignored", indicator: "green" });
            cur_frm.reload_doc();
        },
    });
    console.log("ignoress");
};
