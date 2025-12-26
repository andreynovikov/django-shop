import { createSerializer, parseAsArrayOf, parseAsBoolean, parseAsInteger, parseAsNativeArrayOf, parseAsString } from "nuqs"

export const productSearchParams = {
  id: parseAsNativeArrayOf(parseAsInteger),
  text: parseAsString,
  title: parseAsString,
  instock: parseAsInteger,
  categories: parseAsInteger,
  in_category: parseAsInteger,
  enabled: parseAsBoolean,
  show_on_sw: parseAsBoolean,
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
}

export const productSearchParamsSerializer = createSerializer(productSearchParams)
