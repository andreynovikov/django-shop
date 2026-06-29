import BooleanFilter from './filters/boolean-filter'
import ChoiceFilter from './filters/choice-filter'
import MultipleChoiceFilter from './filters/multiple-choice-filter'
import PriceFilter from './filters/price-filter'
import SliderFilter from './filters/slider-filter'

export default function ProductFilter({ filter, filterValue, onFilterChanged }) {
  const FilterComponent =
    filter.class === 'NullBooleanField' ? BooleanFilter
      : filter.class === 'ChoiceField' ? ChoiceFilter
        : filter.class === 'MultipleChoiceField' ? MultipleChoiceFilter
          : filter.widget === 'ShopRangeWidget' ? PriceFilter
            : filter.widget === 'ShopSliderWidget' ? SliderFilter
              : undefined

  if (FilterComponent === undefined)
    return null

  return <FilterComponent filter={filter} filterValue={filterValue} onFilterChanged={onFilterChanged} />
}
