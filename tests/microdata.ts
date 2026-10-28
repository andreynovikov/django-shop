import { Page } from '@playwright/test'

import { enumerations, schemaTypes } from './schema-org'

export interface MicrodataText {
  value: string
  // where the value is taken from: content attribute, URL attribute (href, src) or text content
  source: 'content' | 'url' | 'text'
}

export interface MicrodataItem {
  type: string[]
  properties: Record<string, MicrodataValue[]>
}

export type MicrodataValue = MicrodataText | MicrodataItem

export const isItem = (value: MicrodataValue): value is MicrodataItem => 'properties' in value

export interface Microdata {
  items: MicrodataItem[]
  // itemprop elements outside of any itemscope, parsers ignore them
  orphans: string[]
}

// Runs in the browser, follows the WHATWG microdata algorithm without itemref (the site doesn't use it).
// Like Google and the Schema Markup Validator, a content attribute takes precedence on any element.
function extractInPage(): Microdata {
  const owner = (element: Element) => element.parentElement?.closest('[itemscope]') ?? null

  const describe = (element: Element) =>
    `<${element.localName} itemprop="${element.getAttribute('itemprop')}"${element.hasAttribute('itemscope') ? ` itemtype="${element.getAttribute('itemtype')}"` : ''}>`

  const value = (element: Element): MicrodataValue => {
    if (element.hasAttribute('itemscope'))
      return item(element)
    if (element.hasAttribute('content'))
      return { value: element.getAttribute('content')!, source: 'content' }
    if (element instanceof HTMLAnchorElement || element instanceof HTMLAreaElement || element instanceof HTMLLinkElement)
      return { value: element.href, source: 'url' }
    if (['audio', 'embed', 'iframe', 'img', 'source', 'track', 'video'].includes(element.localName))
      return { value: (element as HTMLImageElement).src, source: 'url' }
    if (element instanceof HTMLObjectElement)
      return { value: element.data, source: 'url' }
    if (['data', 'meter'].includes(element.localName))
      return { value: element.getAttribute('value') ?? '', source: 'content' }
    if (element instanceof HTMLTimeElement && element.hasAttribute('datetime'))
      return { value: element.dateTime, source: 'content' }
    return { value: (element.textContent ?? '').replace(/\s+/g, ' ').trim(), source: 'text' }
  }

  const item = (scope: Element): MicrodataItem => {
    const properties: Record<string, MicrodataValue[]> = {}
    for (const element of scope.querySelectorAll('[itemprop]'))
      if (owner(element) === scope)
        for (const name of element.getAttribute('itemprop')!.split(/\s+/).filter(Boolean))
          (properties[name] ??= []).push(value(element))
    return { type: (scope.getAttribute('itemtype') ?? '').split(/\s+/).filter(Boolean), properties }
  }

  return {
    items: Array.from(document.querySelectorAll('[itemscope]:not([itemprop])'), item),
    orphans: Array.from(document.querySelectorAll('[itemprop]')).filter((element) => owner(element) === null).map(describe),
  }
}

export async function extractMicrodata(page: Page) {
  return await page.evaluate(extractInPage)
}

// Properties a type needs to be useful for search engines, from Google's structured data requirements
const requiredProperties: Record<string, string[]> = {
  Product: ['name', 'offers'],
  Offer: ['url', 'price', 'priceCurrency', 'availability'],
  Brand: ['name'],
  OfferCatalog: ['name', 'itemListElement'],
  Organization: ['name', 'address'],
  PostalAddress: ['streetAddress', 'addressLocality'],
}

const dataTypes = ['Text', 'URL', 'Number', 'Integer', 'Float', 'Boolean', 'Date', 'DateTime', 'Time']

// Formats of text values the site uses, the vocabulary allows any text for them
const valueFormats: Record<string, RegExp> = {
  price: /^\d+(\.\d+)?$/,
  priceCurrency: /^[A-Z]{3}$/,
  telephone: /^\+?[\d\s()-]+$/,
}

export function typeName(item: MicrodataItem) {
  return item.type[0]?.match(/^https?:\/\/schema\.org\/(\w+)$/)?.[1]
}

function isAbsoluteUrl(value: string) {
  try {
    return ['http:', 'https:'].includes(new URL(value).protocol)
  } catch {
    return false
  }
}

function validateText(name: string, range: string[], text: MicrodataText, path: string, problems: string[]) {
  if (text.value === '') {
    problems.push(`${path}: empty value`)
    return
  }

  const enumeration = range.find((type) => type in enumerations)
  if (enumeration !== undefined) {
    const member = text.value.match(/^https?:\/\/schema\.org\/(\w+)$/)?.[1]
    if (member === undefined || !enumerations[enumeration].includes(member))
      problems.push(`${path}: "${text.value}" is not a schema.org ${enumeration} value`)
    return
  }

  if (!range.some((type) => dataTypes.includes(type)))
    problems.push(`${path}: expects an item of ${range.join(' or ')}, got text "${text.value}"`)
  else if (range.includes('URL') && !range.includes('Text')) {
    if (!isAbsoluteUrl(text.value))
      problems.push(`${path}: "${text.value}" is not an absolute URL`)
  } else if (text.source === 'url' && !range.includes('URL'))
    problems.push(`${path}: text value is taken from a URL attribute: "${text.value}"`)
  else if (name in valueFormats && !valueFormats[name].test(text.value))
    problems.push(`${path}: "${text.value}" is not a valid ${name}`)
}

function validateItem(item: MicrodataItem, path: string, problems: string[]) {
  const name = typeName(item)
  if (item.type.length !== 1 || name === undefined) {
    problems.push(`${path}: itemtype should be a single schema.org type, got "${item.type.join(' ')}"`)
    return
  }
  const type = schemaTypes[name]
  if (type === undefined) {
    problems.push(`${path}: ${name} is not in tests/schema-org.ts`)
    return
  }

  for (const property of requiredProperties[name] ?? [])
    if (!(property in item.properties))
      problems.push(`${path}: ${name} has no ${property}`)

  for (const [property, values] of Object.entries(item.properties)) {
    const range = type.properties[property]
    if (range === undefined) {
      problems.push(`${path}: ${property} is not a property of ${name}`)
      continue
    }
    values.forEach((value, index) => {
      const valuePath = `${path}.${property}` + (values.length > 1 ? `[${index}]` : '')
      if (!isItem(value))
        validateText(property, range, value, valuePath, problems)
      else {
        const valueType = typeName(value)
        const valueTypes = valueType === undefined ? [] : [valueType, ...(schemaTypes[valueType]?.ancestors ?? [])]
        if (valueType !== undefined && !valueTypes.some((type) => range.includes(type)))
          problems.push(`${valuePath}: expects ${range.join(' or ')}, got ${valueType}`)
        validateItem(value, valuePath, problems)
      }
    })
  }
}

// Problems of the page microdata as readable messages, so a failing test lists all of them.
// Repeated items such as product cards have the same problems, they are reported once with a count.
export function validateMicrodata({ items, orphans }: Microdata) {
  const problems = orphans.map((orphan) => `${orphan} is outside of any itemscope`)
  items.forEach((item, index) => validateItem(item, `${typeName(item) ?? 'item'}[${index}]`, problems))

  const groups = new Map<string, { first: string, count: number }>()
  for (const problem of problems) {
    // values differ between items, so only the path and the kind of problem are compared
    const key = problem.replace(/\[\d+\]/g, '').replace(/"[^"]*"/g, '""')
    const group = groups.get(key)
    if (group === undefined)
      groups.set(key, { first: problem, count: 1 })
    else
      group.count++
  }
  return Array.from(groups.values(), ({ first, count }) => count > 1 ? `${first} (and ${count - 1} more)` : first)
}
