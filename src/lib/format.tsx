import { CategoryBrief, Country, Manufacturer, Product, ProductImage, ProductInfo, SalesAction } from './types'

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

// we need to accept all types for TypeScript to be happy, but we do not in fact process all product fields
export function prettifyProductFieldValue(field: keyof Product, value: string | number | boolean | Country | string[] | ProductImage[] | number[] | CategoryBrief[] | ProductInfo[] | SalesAction[] | Manufacturer | undefined) {
  if (value === undefined)
    return ""
  if (field === 'manufacturer')
    return (value as Manufacturer).name
  if (field === 'country' || field === 'developer_country')
    return (value as Country).enabled ? (value as Country).name : ""
  if (field === 'complect')
    return <div dangerouslySetInnerHTML={{ __html: value }} />
  if (typeof value === 'boolean')
    return value ? 'да' : 'нет'
  if (typeof value === 'string')
    return value.trim()
  return value as number
}