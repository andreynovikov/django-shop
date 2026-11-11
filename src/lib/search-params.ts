import {
  createParser,
  createLoader,
  createSerializer,
  parseAsBoolean,
  parseAsInteger,
  parseAsNativeArrayOf,
  parseAsString,
  inferParserType,
  createSearchParamsCache,
} from 'nuqs/server'

const parseAsBooleanExtended = createParser({
  parse(value) {
    // Treat an empty string (?flag) or "true" (?flag=true) or "1" (?flag=1) as true
    if (value === '' || value === 'true' || value === '1') return true
    if (value === 'false' || value === '0') return false
    return null
  },
  serialize(value) {
    return value ? 'true' : 'false'
  }
})

// Lowest and highest price, price=1000-5000. The backend refuses a range without both bounds, so a query
// that has only one, e.g. from a cut link, leaves the price unset.
const parseAsPriceRange = createParser({
  parse(value) {
    const match = /^(\d+)-(\d+)$/.exec(value)
    return match === null ? null : [Number(match[1]), Number(match[2])]
  },
  serialize: (value: number[]) => value.join('-'),
  eq: (a, b) => a.length === b.length && a.every((bound, index) => bound === b[index]),
})

export const advertSearchParams = {
  category: parseAsInteger,
  places: parseAsNativeArrayOf(parseAsString),
}

export const advertSearchParamsSerializer = createSerializer(advertSearchParams)

export const blogEntrySearchParams = {
  page: parseAsInteger.withDefault(1),
  categories: parseAsInteger,
  tags: parseAsString,
}

export type BlogSearchParamsType = Partial<inferParserType<typeof blogEntrySearchParams>>
export const blogEntrySearchParamsSerializer = createSerializer(blogEntrySearchParams)

export const categorySearchParams = {
  feed: parseAsBoolean,
}

export type CategorySearchParamsType = Partial<inferParserType<typeof categorySearchParams>>
export const categorySearchParamsSerializer = createSerializer(categorySearchParams)

export const comparisonSearchParams = {
  kind: parseAsInteger,
}

export const comparisonSearchParamsSerializer = createSerializer(comparisonSearchParams)

export const kindSearchParams = {
  product: parseAsNativeArrayOf(parseAsInteger),
}

export type KindSearchParamsType = Partial<inferParserType<typeof kindSearchParams>>
export const kindSearchParamsSerializer = createSerializer(kindSearchParams)

export const productSearchParams = {
  id: parseAsNativeArrayOf(parseAsInteger),
  text: parseAsString,
  title: parseAsString,
  instock: parseAsInteger,
  categories: parseAsInteger,
  in_category: parseAsNativeArrayOf(parseAsInteger),
  variations: parseAsString,
  enabled: parseAsBoolean,
  show_on_sw: parseAsBoolean,
  isnew: parseAsBoolean,
  gift: parseAsBoolean,
  recomended: parseAsBoolean,
  firstpage: parseAsBoolean,
  price: parseAsPriceRange,
  kind: parseAsNativeArrayOf(parseAsInteger),
  manufacturer: parseAsNativeArrayOf(parseAsInteger),

  sm_alphabet_bool: parseAsBoolean,
  sm_autobuttonhole_bool: parseAsBoolean,
  sm_dualtransporter_bool: parseAsBoolean,
  sm_threader_bool: parseAsBoolean,
  sm_power: parseAsInteger,
  sm_stitchquantity: parseAsInteger,
  sm_shuttletype: parseAsString,

  page: parseAsInteger.withDefault(1),
  page_size: parseAsInteger,
  ordering: parseAsString,
  for_xml: parseAsBoolean,

  ta: parseAsInteger,
}

export type ProductSearchParamsType = Partial<inferParserType<typeof productSearchParams>>
export const productSearchParamsSerializer = createSerializer(productSearchParams)
export const productSearchParamsLoader = createLoader(productSearchParams)

export const orderSearchParams = {
  page: parseAsInteger.withDefault(1),
  filter: parseAsString,
  site: parseAsInteger,
}

export const orderSearchParamsSerializer = createSerializer(orderSearchParams)

export const salesActionProductsSearchParams = {
  page: parseAsInteger.withDefault(1),
  page_size: parseAsInteger,
}

export const salesActionProductsSearchParamsSerializer = createSerializer(salesActionProductsSearchParams)

export const storeSearchParams = {
  marketplace: parseAsBooleanExtended,
  lottery: parseAsBooleanExtended,
}

export type StoreSearchParamsType = Partial<inferParserType<typeof storeSearchParams>>
export const storeSearchParamsSerializer = createSerializer(storeSearchParams)
export const storeSearchParamsCache = createSearchParamsCache(storeSearchParams)
export const storeSearchParamsLoader = createLoader(storeSearchParams)
