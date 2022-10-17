import Script from 'next/script';

import BooleanFilter from './filters/boolean-filter';
import ChoiceFilter from './filters/choice-filter';
import MultipleChoiceFilter from './filters/multiple-choice-filter';
import PriceFilter from './filters/price-filter';
import SliderFilter from './filters/slider-filter';

export default function ProductFilter({filter, onFilterChanged}) {
    if (filter.class === 'NullBooleanField')
        return <BooleanFilter filter={filter} onFilterChanged={onFilterChanged} />

    if (filter.class === 'ChoiceField')
        return <ChoiceFilter filter={filter} onFilterChanged={onFilterChanged} />

    if (filter.class === 'MultipleChoiceField')
        return <MultipleChoiceFilter filter={filter} onFilterChanged={onFilterChanged} />

    if (filter.widget === 'PriceWidget')
        return <PriceFilter filter={filter} onFilterChanged={onFilterChanged} />

    if (filter.widget === 'ShopSliderWidget')
        return <SliderFilter filter={filter} onFilterChanged={onFilterChanged} />

    return null;
}
