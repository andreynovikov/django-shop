import {
  createParser,
  createLoader,
  createSerializer,
  parseAsArrayOf,
  parseAsBoolean,
  parseAsInteger,
  parseAsNativeArrayOf,
  parseAsString,
  inferParserType,
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
  price: parseAsArrayOf(parseAsInteger, '-'),
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

export const productSearchParamsSerializer = createSerializer(productSearchParams)
export const productSearchParamsLoader = createLoader(productSearchParams)

export const orderSearchParams = {
  page: parseAsInteger.withDefault(1),
  filter: parseAsString,
  site: parseAsInteger,
}

export const orderSearchParamsSerializer = createSerializer(orderSearchParams)

export const storeSearchParams = {
  marketplace: parseAsBooleanExtended,
  lottery: parseAsBooleanExtended,
}

export type StoreSearchParamsType = Partial<inferParserType<typeof storeSearchParams>>
export const storeSearchParamsSerializer = createSerializer(storeSearchParams)
export const storeSearchParamsLoader = createLoader(storeSearchParams)
