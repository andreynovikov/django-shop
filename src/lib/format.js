export function formatPhone(phone) {
    const match = phone.match(/(\+7)(\d{3})(\d{2,3})(\d{2})(\d{2})/);
    if (match === null)
        return phone;
    return "{1} ({2}) {3}-{4}-{5}".replace(/{([0-9]+)}/g, function (m, i) {
        return typeof match[i] == 'undefined' ? m : match[i];
    });
}

