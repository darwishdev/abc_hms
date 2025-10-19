frappe.realtime.on("handle_error", function ({ message, type, frm }) {
    console.log("errorrrrr", message, type);
    frm["ignore_availability"] = type == "Availability" ? true : frm["ignore_availability"];
    frm["allow_share"] = type == "Room Sharing" ? true : frm["allow_share"];
    let btn_label = type == "Room Sharing" ? "Allow Share" : "Ignore Availability";
    frappe.warn(
        type,
        message,
        () => {
            frappe.call("abc_hms.ignore_and_resave", { args: frm });
        },
        btn_label,
    );
});
function reset_discount_fields(frm) {
    frm.set_value("discount_type", "");
    frm.set_value("discount_percent", 0);
    frm.set_value("discount_amount", 0);
    frm.set_value("fixed_rate", false);
}
function set_room_filter(frm) {
    //frm.set_query("room", function () {
    //    return {
    //        filters: {
    //            room_type: frm.doc.room_type,
    //        },
    //    };
    //});
}
frappe.ui.form.on("Reservation", {
    onload(frm) {
        if (frm.doc.room_type) {
            set_room_filter(frm);
        }
        frm.dateController = window.createDateRangeController({
            fromKey: "arrival",
            nightsKey: "nights",
            toKey: "departure",
            get: (key) => frm.doc[key],
            set: (key, value) => frm.set_value(key, value),
        });

        if (frm.doc.property) {
            frm.call("get_business_date").then(({ message }) => {
                frm._current_business_date = message;
                handle_check_in(frm);
                handle_reverse_check_in(frm);
                handle_check_out(frm);
                handle_early_checkin(frm);
                handle_early_checkout(frm);
                handle_reinstate(frm);
            });
        }
        setTimeout(() => {
            handle_reservation_days_button(frm);
        }, 100);
    },

    refresh(frm) {
        if (frm.doc.property) {
            frm.call("get_business_date").then(({ message }) => {
                frm._current_business_date = message;
                handle_check_in(frm);
                handle_reverse_check_in(frm);
                handle_check_out(frm);
                handle_early_checkin(frm);
                handle_early_checkout(frm);
                handle_reinstate(frm);
            });
        }

        handle_availability_button(frm);
    },
    property(frm) {
        frm.call("get_business_date").then(({ message }) => {
            frm._current_business_date = message;
            if (!frm.doc.created_on_business_date) {
                frm.frm.doc.created_on_business_date = frm._current_business_date;
            }
        });
        handle_availability_button(frm);
    },
    room_type(frm) {
        reservation_availability_check(frm);
        // if (frm.doc.room_type) {
        //     set_room_filter(frm);
        // }
    },
    rate_code(frm) {
        reservation_availability_check(frm);
    },
    arrival(frm) {
        validate_arrival(frm);
        frm.dateController?.update("arrival");
    },
    nights(frm) {
        frm.dateController?.update("nights");
    },

    departure(frm) {
        handle_availability_button(frm);
        frm.dateController?.update("departure");
    },
    base_rate(frm) {
        const total_stay = frm.doc.base_rate * frm.doc.nights;
        frm.set_value("total_stay", total_stay);
        if (frm._ignore_discount_events) return;
        set_ignore_discount(frm);
        console.log(frm.doc, frm.doc.rate_code_rate);
        const { discount_type, rate_code_rate, base_rate } = frm.doc;
        const is_rate_changed = rate_code_rate != base_rate;
        if (!is_rate_changed) {
            reset_discount_fields(frm);
            reservation_availability_check(frm);
            set_ignore_discount(frm, false, 500);
            return;
        }
        if (base_rate > rate_code_rate) {
            reset_discount_fields(frm);
            frm.set_value("fixed_rate", true);
            //reservation_availability_check(frm);
            set_ignore_discount(frm, false, 500);
            return;
        }
        if (!discount_type) frm.set_value("discount_type", "Percent");
        const discount_amount = rate_code_rate - base_rate;
        const discount_percent = (discount_amount / rate_code_rate) * 100;
        //reservation_availability_check(frm);
        frm.set_value("discount_amount", discount_amount);
        frm.set_value("discount_percent", discount_percent);
        set_ignore_discount(frm, false, 500);
        // frm.call("apply_discount", { changed_field: arguments.callee.name });
    },

    discount_percent(frm) {
        if (frm._ignore_discount_events) return;
        set_ignore_discount(frm);
        const { discount_percent, rate_code_rate } = frm.doc;
        if (discount_percent == 0) {
            reset_discount_fields(frm);
            set_ignore_discount(frm, false, 500);
            reservation_availability_check(frm);
            return;
        }
        if (discount_percent < 0 || discount_percent > 100) {
            frm.set_value("discount_percent", 0);
            frappe.throw("Please Enter Valid Percent");
            set_ignore_discount(frm, false, 500);
            reservation_availability_check(frm);
            return;
        }
        const discount_amount = (discount_percent * rate_code_rate) / 100;
        frm.set_value("discount_amount", discount_amount);
        frm.set_value("base_rate", rate_code_rate - discount_amount);
        reservation_availability_check(frm);
        set_ignore_discount(frm, false, 500);
    },
    discount_amount(frm) {
        if (frm._ignore_discount_events) return;
        set_ignore_discount(frm);
        const { discount_amount, rate_code_rate } = frm.doc;
        if (discount_amount == 0) {
            reset_discount_fields(frm);
            set_ignore_discount(frm, false, 500);
            reservation_availability_check(frm);
            return;
        }
        if (discount_amount > rate_code_rate) {
            frm.set_value("discount_amount", 0);
            frappe.throw("Discount amount should be less than the base rate");
            set_ignore_discount(frm, false, 500);
            reservation_availability_check(frm);
            return;
        }
        const discount_percent = (discount_amount / rate_code_rate) * 100;
        frm.set_value("discount_percent", discount_percent);
        frm.set_value("base_rate", rate_code_rate - discount_amount);
        reservation_availability_check(frm);
        set_ignore_discount(frm, false, 500);
    },
});

const handle_reservation_days_button = (frm) => {
    const can_show =
        frm.doc.property && frm.doc.docstatus === 1 && frm.doc.reservation_status == "In House";

    if (!can_show) {
        frm.remove_custom_button(__("View Daily Details"));
        return;
    }
    frm.add_custom_button(__("View Daily Details"), async () => {
        frappe
            .call("abc_hms.reservation_date_list", { reservation: frm.doc.name })
            .then(({ message: data }) => {
                const dialog = new frappe.ui.Dialog({
                    title: __("Reservation Breakdown"),
                    size: "extra-large",

                    fields: [
                        {
                            fieldname: "reservation_dates",
                            fieldtype: "Table",
                            label: __("Reservation Breakdown"),

                            cannot_delete_rows: 1,
                            // in_place_edit: true,
                            reqd: 1,
                            fields: [
                                {
                                    fieldname: "room_type",
                                    label: __("Room Type"),
                                    fieldtype: "Link",
                                    in_list_view: 1,
                                    options: "Room Type",
                                    reqd: 1,
                                },
                                {
                                    fieldname: "rate_code",
                                    label: __("Rate Code"),
                                    fieldtype: "Link",
                                    in_list_view: 1,
                                    options: "Rate Code",
                                    reqd: 1,
                                },
                                {
                                    fieldname: "room",
                                    label: __("Room"),
                                    fieldtype: "Link",
                                    in_list_view: 1,
                                    options: "Room",
                                    reqd: 0,
                                },
                                {
                                    fieldname: "rate_code_rate",
                                    label: __("Rate Code Rate"),
                                    fieldtype: "Currency",
                                    reqd: 0,
                                },
                                {
                                    fieldname: "base_rate",
                                    label: __("Base Rate"),
                                    fieldtype: "Currency",
                                    in_list_view: 1,
                                    reqd: 0,
                                },
                                {
                                    fieldname: "discount_type",
                                    label: __("Discount Type"),
                                    fieldtype: "Select",
                                    options: "\nPercentage\nAmount",
                                    reqd: 0,
                                },
                                {
                                    fieldname: "discount_value",
                                    label: __("Discount Value"),
                                    fieldtype: "Float",
                                    reqd: 0,
                                },
                                {
                                    fieldname: "for_date",
                                    label: __("Day"),
                                    fieldtype: "Date",
                                    options: "Rom",
                                    read_only: 1,
                                    in_list_view: 1,
                                    reqd: 0,
                                },
                            ],
                        },
                    ],
                });
                dialog.fields_dict["reservation_dates"].df.data = data;
                dialog.fields_dict["reservation_dates"].refresh();
                dialog.set_primary_action(__("Create"), () => {
                    const values = dialog.get_values();
                    if (!values) return;

                    // call backend
                    frappe.call({
                        method: "abc_hms.reservation_date_bulk_upsert",
                        args: {
                            reservation_dates: values.reservation_dates,
                        },
                        freeze: true,
                        freeze_message: __("Saving Reservation Dates..."),
                        callback: (r) => {
                            if (!r.exc) {
                                frappe.show_alert({
                                    message: __("Reservation Dates Updated Successfully"),
                                    indicator: "green",
                                });
                                dialog.hide();
                                frm.reload_doc();
                            }
                        },
                    });
                });
                dialog.show();
            });
        // await reservation_availability_check(frm);
    });
};
const handle_availability_button = (frm) => {
    const can_show =
        frm.doc.property && frm.doc.docstatus === 0 && frm.doc.arrival && frm.doc.departure;

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

const reservation_availability_check = async (frm) => {
    if (!frm) return;
    if (!frm.fields_dict) return;
    const wrapper = frm.fields_dict.availability_html.$wrapper;
    frm.call("get_availability").then((result) => {
        if (result.message) {
            show_availability(wrapper, result.message);
            wrapper.data("frm", frm);
        }
    });
};
const validate_arrival = (frm) => {
    const _current_business_date = frm._current_business_date;
    const { arrival } = frm.doc;
    if (!_current_business_date) {
        frm.set_value("arrival", "");
        frappe.throw("Please Choose Property First");
        return;
    }
    if (
        arrival &&
        arrival < _current_business_date &&
        reservation_status != "In House" &&
        reservation_status != "Departure"
    ) {
        frm.set_value("arrival", "");
        frappe.throw(
            __(`Arrival date cannot be before business date (${_current_business_date}).`),
        );
    }
};
const set_ignore_discount = (frm, value = true, delay = 0) => {
    if (value) {
        frm._ignore_discount_events = true;
    }
    setTimeout(() => {
        frm._ignore_discount_events = false;
    }, delay);
};
const date_to_int = (date) => {
    return parseInt(date.replace(/-/g, ""));
};
const update_reservation_status = (frm, new_status, msg) => {
    frm.call("reservation_status_update", { new_status }).then(() => {
        frappe.show_alert({
            message: __(msg),
            indicator: "green",
        });
        frm.reload();
    });
};

const handle_reverse_check_in = (frm) => {
    const { docstatus, reservation_status, arrival, name, room, guest } = frm.doc;
    const _current_business_date = frm._current_business_date;

    const can_show =
        date_to_int(arrival) == date_to_int(_current_business_date) &&
        room.length > 0 &&
        reservation_status == "In House";
    docstatus == 1;
    if (!can_show) {
        frm.remove_custom_button(__("Reverse Check In"));
        return;
    }

    frm.add_custom_button(__("Reverse Check In"), () => {
        frappe.confirm(
            `Reverse Check-in Guest: ${guest}. from Room: ${room}. for Reservation: ${name}`,
            () => {
                update_reservation_status(frm, "Arrival", "Guest Check In Reversed Successfully");
            },
            () => {
                // action to perform if No is selected
            },
        );
    });
};
const handle_check_in = (frm) => {
    const { docstatus, reservation_status, arrival, name, room, guest } = frm.doc;
    const _current_business_date = frm._current_business_date;
    const can_show =
        date_to_int(arrival) == date_to_int(_current_business_date) &&
        room.length > 0 &&
        ["Arrival", "Confirmed"].includes(reservation_status);

    if (!can_show) {
        frm.remove_custom_button(__("Check In"));
        frm.remove_custom_button(__("Mark No Show"));
        return;
    }

    frm.add_custom_button(__("Mark Now Show"), async () => {
        console.log("No Show in");
    });
    frm.add_custom_button(__("Check In"), () => {
        frappe.confirm(
            `Check-in Guest: ${guest}. into Room: ${room}. for Reservation: ${name}`,
            () => {
                update_reservation_status(frm, "In House", "Guest Checked In Successfully");
            },
            () => {
                // action to perform if No is selected
            },
        );
        console.log("checking in");
    });
};

const handle_check_out = (frm) => {
    const { departure, reservation_status, guest, room, name } = frm.doc;
    const _current_business_date = frm._current_business_date;
    //const _current_folio_balance = frm._current_folio_balance;

    const can_show =
        date_to_int(departure) == date_to_int(_current_business_date) &&
        reservation_status == "In House";
    if (!can_show) {
        frm.remove_custom_button(__("Check Out"));
        return;
    }
    frm.add_custom_button(__("Check Out"), async () => {
        frm.call("reservation_folio_find").then((resp) => {
            const { balance, folio_name } = resp.message;
            if (balance > 1) {
                frappe.throw(`
    The current folio balance is ${balance}.
    Please <a href="http://localhost:5173/folio/${folio_name}"
        target="_blank"
        style="font-weight:600; color:#007bff; text-decoration:underline;">
        open the folio
    </a> to settle it before checking out the guest.
`);
            }
            frappe.confirm(
                `Check-Out Guest: ${guest}. From Room: ${room}. for Reservation: ${name}`,
                () => {
                    update_reservation_status(
                        frm,
                        "Checked Out",
                        "Guest Checked Out Successfully",
                    );
                },
                () => {
                    // action to perform if No is selected
                },
            );
        });
    });
};
const handle_reinstate = (frm) => {
    const { departure, reservation_status, guest, room, name } = frm.doc;
    const _current_business_date = frm._current_business_date;

    // show only when departure == business date and guest is Checked Out
    const can_show =
        date_to_int(departure) == date_to_int(_current_business_date) &&
        reservation_status === "Checked Out";

    if (!can_show) {
        frm.remove_custom_button(__("Reinstate"));
        return;
    }

    // add button (will be deduped if already added because we always remove when !can_show)
    frm.add_custom_button(__("Reinstate"), async () => {
        // confirm with the user
        frappe.confirm(
            `Reinstate Guest: ${guest}. Back to Room: ${room}. for Reservation: ${name}?`,
            () => {
                // Yes callback -> update status to In House
                update_reservation_status(frm, "In House", "Guest reinstated successfully");
            },
            () => {
                // No callback -> do nothing
            },
        );
    });
};

const date_diff_days = (date1_int, date2_int) => {
    const d1 = new Date(
        Math.floor(date1_int / 10000),
        Math.floor((date1_int % 10000) / 100) - 1,
        date1_int % 100,
    );
    const d2 = new Date(
        Math.floor(date2_int / 10000),
        Math.floor((date2_int % 10000) / 100) - 1,
        date2_int % 100,
    );

    return Math.floor((d1 - d2) / (1000 * 60 * 60 * 24));
};
const handle_early_checkin = (frm) => {
    const { reservation_status, arrival, nights, guest, room, name } = frm.doc;
    const _current_business_date = frm._current_business_date;
    const arrival_int = date_to_int(arrival);
    const current_date_int = date_to_int(_current_business_date);
    const days_until_arrival = date_diff_days(arrival_int, current_date_int);
    const new_nights = nights + days_until_arrival;
    const can_show = days_until_arrival > 0 && reservation_status == "Confirmed";

    if (!can_show) {
        frm.remove_custom_button(__("Early Check-in"));
        return;
    }

    frm.add_custom_button(__("Early Check-in"), async () => {
        frappe.confirm(
            `Early Check-in: ${guest}.  to Room: ${room}. for Reservation: ${name}?\n Please Note that this action will affect the arrival date of the reservation\n New Arrival date will become ${_current_business_date} and Length Of Stay will become ${new_nights}`,
            () => {
                frm.set_value("arrival", _current_business_date);
                frm.set_value("nights", new_nights);
                update_reservation_status(frm, "In House", "Guest checked-in successfully");
            },
            () => {
                // No callback -> do nothing
            },
        );
    });
};

const handle_early_checkout = (frm) => {
    const { departure, name, guest, room, reservation_status, nights } = frm.doc;
    const _current_business_date = frm._current_business_date;
    const departure_int = date_to_int(departure);
    const current_date_int = date_to_int(_current_business_date);
    const days_until_departure = date_diff_days(departure_int, current_date_int);
    const new_nights = nights - days_until_departure;
    const can_show = departure_int > current_date_int && reservation_status == "In House";

    if (!can_show) {
        frm.remove_custom_button(__("Early Checkout"));
        return;
    }

    frm.add_custom_button(__("Early Checkout"), async () => {
        frappe.confirm(
            `Early Check-out: ${guest}.  from Room: ${room}. for Reservation: ${name}?\n Please Note that this action will affect the departure date of the reservation\n New Departure date will become ${_current_business_date} and Length Of Stay will become ${new_nights}`,
            () => {
                frm.set_value("departure", _current_business_date);
                frm.set_value("nights", new_nights);
                update_reservation_status(frm, "Checked Out", "Guest checked-out successfully");
            },
            () => {
                // No callback -> do nothing
            },
        );
    });
};
