import BooleanFilter from './filters/boolean-filter'
import ChoiceFilter from './filters/choice-filter'
import MultipleChoiceFilter from './filters/multiple-choice-filter'
import PriceFilter from './filters/price-filter'
import SliderFilter from './filters/slider-filter'
import { ProductFilterField } from './filters/types'

interface ProductFilterProps {
  filter: ProductFilterField
  filterValue: unknown
  onFilterChanged: (name: string, value: unknown) => void
}

export default function ProductFilter({ filter, filterValue, onFilterChanged }: ProductFilterProps) {
  // the value is parsed from the query by productSearchParams, whose parser for a filter matches its class
  const props = { filter, onFilterChanged }

  if (filter.class === 'NullBooleanField')
    return <BooleanFilter {...props} filterValue={filterValue as boolean | null} />
  if (filter.class === 'ChoiceField')
    return <ChoiceFilter {...props} filterValue={filterValue as string | number | null} />
  if (filter.class === 'MultipleChoiceField')
    return <MultipleChoiceFilter {...props} filterValue={filterValue as Array<string | number> | null} />
  if (filter.widget === 'ShopRangeWidget')
    return <PriceFilter {...props} filterValue={filterValue as number[] | null} />
  if (filter.widget === 'ShopSliderWidget')
    return <SliderFilter {...props} filterValue={filterValue as number | null} />
  return null
}
