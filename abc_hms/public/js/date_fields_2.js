function createDateRangeController({
    get,
    set,
    fromKey = "from",
    toKey = "to",
    nightsKey = "nights",
}) {
    let _updating = false;

    function parseIntSafe(v) {
        const n = Number(v);
        return Number.isFinite(n) ? Math.floor(n) : null;
    }

    function addDaysToDateString(dateStr, days) {
        if (!dateStr) return null;
        const d = frappe.datetime.str_to_obj(dateStr);
        d.setDate(d.getDate() + days);
        return frappe.datetime.obj_to_str(d);
    }

    function update(changedBy) {
        if (_updating) return;
        _updating = true;

        try {
            const from = get(fromKey);
            const to = get(toKey);
            const nightsRaw = get(nightsKey);
            const nights = parseIntSafe(nightsRaw);

            const safeSet = (key, value) => {
                if (value == null) return;
                const cur = get(key);
                if (String(cur) !== String(value)) set(key, value);
            };

            if (changedBy === fromKey) {
                if (from && Number.isFinite(nights)) {
                    safeSet(toKey, addDaysToDateString(from, nights));
                    return;
                }
                if (from && to) {
                    const diff = frappe.datetime.get_day_diff(to, from);
                    if (diff >= 0) safeSet(nightsKey, diff);
                }
                if (from && !nightsRaw && !to) {
                    safeSet(nightsKey, 1);
                    safeSet(toKey, addDaysToDateString(from, 1));
                    return;
                }
                return;
            }
            if (changedBy === nightsKey) {
                if (from && Number.isFinite(nights)) {
                    safeSet(toKey, addDaysToDateString(from, nights));
                    return;
                }
                if (to && Number.isFinite(nights)) {
                    safeSet(fromKey, addDaysToDateString(to, -nights));
                    return;
                }
                return;
            }
            if (changedBy === toKey) {
                if (from && to) {
                    if (to < from) {
                        safeSet(nightsKey, 0);
                        safeSet(fromKey, to);
                        return;
                    }
                    const diff = frappe.datetime.get_day_diff(to, from);
                    if (diff >= 0) safeSet(nightsKey, diff);
                    return;
                }
                if (Number.isFinite(nights) && to) {
                    safeSet(fromKey, addDaysToDateString(to, -nights));
                }
            }
        } finally {
            _updating = false;
        }
    }

    return { update };
}

window.createDateRangeController = createDateRangeController;
