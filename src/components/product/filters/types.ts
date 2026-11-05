import { CategoryFilter, ProductFilterFacet } from '@/lib/types'

// Category filter with the choices and ranges of the current product list
export type ProductFilterField = CategoryFilter & Omit<ProductFilterFacet, 'id'>

// A filter takes only the fields it uses, so the search page can build them by hand. Null means unset.
export interface FilterProps<Field extends keyof ProductFilterField, Value> {
  filter: Pick<ProductFilterField, Field>
  filterValue: Value | null
  onFilterChanged: (name: string, value: Value | null) => void
}
