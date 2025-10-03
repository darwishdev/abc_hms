frappe.ui.form.on("Reservation", {
    onload(frm) {
        if (frm.doc.room_type) {
            frm.set_query("room", function () {
                return {
                    filters: {
                        room_type: frm.doc.room_type,
                    },
                };
            });
        }
    },
    refresh(frm) {
        handle_availability_button(frm);
    },
    property(frm) {
        frm.call("get_business_date");
        handle_availability_button(frm);
    },
    validate(frm) {
        validate_reservation(frm);
    },
    room_type(frm) {
        frm.set_query("room", function () {
            return {
                filters: {
                    room_type: frm.doc.room_type,
                },
            };
        });
    },
    arrival(frm) {
        validate_arrival(frm);
        frm.set_value("nights", 1);
        if (frm.doc.arrival && (!frm.doc.nights || frm.doc.nights == 0)) {
            frm.set_value("nights", 1);
            return;
        }
        frm.call("sync_arrival_departure_nights", { changed_field: arguments.callee.name }).then(
            () => {
                handle_availability_button(frm);
            },
        );
    },
    departure(frm) {
        handle_availability_button(frm);
        try {
            validate_departure(frm);
            frm.call("sync_arrival_departure_nights", { changed_field: arguments.callee.name });
        } catch (error) {
            console.log("validation error");
            return;
        }
    },
    base_rate(frm) {
        if (frm.doc.base_rate != frm.doc.rate_code_rate) {
            frm.set_value("fixed_rate", true);
        }
        frm.call("apply_discount", { changed_field: arguments.callee.name });
    },
    nights(frm) {
        validate_nights(frm);
        console.log("nights changed");
        frm.call("sync_arrival_departure_nights", { changed_field: arguments.callee.name });
        // sync_departure_from_nights(frm);
        handle_availability_button(frm);
    },

    discount_percent(frm) {
        frm.call("apply_discount", { changed_field: arguments.callee.name });
        // validate_number_of_rooms(frm);
    },
    discount_amount(frm) {
        frm.call("apply_discount", { changed_field: arguments.callee.name });
        // validate_number_of_rooms(frm);
    },
    number_of_rooms(frm) {
        frm.call("recalc", { changed_field: arguments.callee.name });
        // validate_number_of_rooms(frm);
    },
});

const handle_availability_button = (frm) => {
    console.log("ahndling availability_html");
    frm.add_custom_button(__("Sync Folios"), async () => {
        frm.call("ensure_all_folios");
    });
    const can_show =
        frm.doc.property &&
        frm.doc.docstatus === 0 &&
        frm.doc.arrival &&
        frm.doc.departure &&
        frm.doc.nights > 0;

    console.log(
        "ahndling availability_html",
        frm.doc,
        can_show,
        frm.doc.property,
        frm.doc.docstatus,
        frm.doc.arrival,
        frm.doc.departure,
        frm.doc.nights,
    );
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
    const { arrival, created_on_business_date } = frm.doc;
    if (!created_on_business_date) {
        frm.set_value("arrival", "");
        frappe.throw("Please Choose Property First");
        return;
    }
    if (
        arrival &&
        arrival < created_on_business_date &&
        reservation_status != "In House" &&
        reservation_status != "Departure"
    ) {
        frm.set_value("arrival", "");
        frappe.throw(
            __(`Arrival date cannot be before business date (${created_on_business_date}).`),
        );
    }
};

const validate_departure = (frm) => {
    const { arrival, departure, reservation_status } = frm.doc;
    if (arrival && departure && departure <= arrival && reservation_status != "In House") {
        frm.call("recalc", { changed_field: "arrival" });
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

function hide_checkin_button(frm) {
    frm.call("validate_room_status")
        .then((r) => {
            console.log(r.message);
            let $btn = frm.page.btn_secondary.find(`button:contains("Check In")`);
            if ($btn.length) {
                $btn.hide();
            }
        })
        .catch((err) => {
            frappe.show_alert({
                message: __("Error while checking room availability: {0}", [err.message]),
                indicator: "red",
            });
        });
}
