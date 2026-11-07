import { Slider } from '@base-ui/react/slider'

import { sliderControlClass, sliderIndicatorClass, sliderThumbClass, sliderTrackClass } from '@/components/ui/slider'

import { FilterProps } from './types'

export default function SliderFilter({ filter, filterValue, onFilterChanged }: FilterProps<'name' | 'unit' | 'attrs', number>) {
  const minValue = filter.attrs?.min_value || 0
  const currentValue = filterValue ?? minValue

  const handleValueChange = (value: number) => {
    if (value === minValue)
      onFilterChanged(filter.name, null)
    else
      onFilterChanged(filter.name, value)
  }

  return (
    <div className="flex items-center">
      <Slider.Root
        thumbAlignment="edge"
        value={currentValue}
        onValueChange={handleValueChange}
        min={minValue}
        max={filter.attrs?.max_value}
        step={filter.attrs?.step || 1}
        className="grow"
      >
        <Slider.Control className={sliderControlClass}>
          <Slider.Track className={sliderTrackClass}>
            <Slider.Indicator className={sliderIndicatorClass} />
            <Slider.Thumb className={sliderThumbClass} />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <div className="ms-2 text-sm">
        <span>{currentValue}</span>
        {filter.unit && <span>&nbsp;{filter.unit}</span>}
      </div>
    </div>
  )
}
