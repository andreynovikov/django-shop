export function formatPhone(phone: string) {
  const match = phone.match(/(\+7)(\d{3})(\d{2,3})(\d{2})(\d{2})/)
  if (match === null)
    return phone
  return "{1} ({2}) {3}-{4}-{5}".replace(/{([0-9]+)}/g, function (m, i) {
    return typeof match[i] == 'undefined' ? m : match[i]
  })
}

export interface PhoneEntry {
  label: string   // text before the number, e.g. "Сервисный центр:"
  number: string  // empty when the entry has no number
  note: string    // text after the number, e.g. "доб.1" or "Промышленный отдел"
  href: string
}

// Phone fields of stores and service centers are free text: several comma separated numbers,
// each may have a label before or a note after it, e.g. "+7 343 360-38-83 Промышленный отдел"
export function parsePhones(phones: string[]): PhoneEntry[] {
  return phones.flatMap((phones) => phones.split(',')).map((phone) => phone.trim()).filter(Boolean).map((phone) => {
    const match = phone.match(/^(.*?)(\+?\(?\d[\d\s()-]*\d)(.*)$/)
    if (match === null)
      return { label: phone, number: '', note: '', href: '' }
    return {
      label: match[1].trim(),
      number: match[2],
      note: match[3].replace(/^[\s.,;]+/, ''),
      href: 'tel:' + match[2].replace(/[^\d+]/g, ''),
    }
  })
}
