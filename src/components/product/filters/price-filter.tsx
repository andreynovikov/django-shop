import { Slider } from '@base-ui/react/slider'

import { sliderControlClass, sliderIndicatorClass, sliderThumbClass, sliderTrackClass } from '@/components/ui/slider'

import { groupedInputClass, inputClass, inputGroupClass } from '@/components/ui/form'

import { FilterProps } from './types'

const addonClass = '-ms-px flex items-center rounded-e-sm border border-gray-400 bg-white px-3 py-[.425rem] text-ms whitespace-nowrap'

export default function PriceFilter({ filter, filterValue, onFilterChanged }: FilterProps<'name' | 'unit' | 'attrs', number[]>) {
  // the scale spans the prices of the products, a bound beyond it (typed or from the query) shows at its end
  const minValue = filter.attrs?.min_value ?? 0
  const maxValue = filter.attrs?.max_value ?? 2000000
  const currentValue = filterValue ?? [minValue, maxValue]

  const handleValueChange = (value: readonly number[]) => {
    // TODO: do not allow negative ranges
    const range = [Math.round(value[0]), Math.round(value[1])]
    if (range[0] !== currentValue[0] || range[1] !== currentValue[1])
      onFilterChanged(filter.name, range)
  }

  // the backend refuses a negative bound or one that is not a number, so such typing is ignored
  const handleBoundInput = (index: number, text: string) => {
    const bound = Number(text)
    if (Number.isFinite(bound) && bound >= 0)
      handleValueChange(index === 0 ? [bound, currentValue[1]] : [currentValue[0], bound])
  }

  return (
    <div>
      <Slider.Root
        thumbAlignment="edge"
        value={currentValue}
        onValueChange={handleValueChange}
        min={minValue}
        max={maxValue}
        step={filter.attrs?.step || 10}
      >
        <Slider.Control className={sliderControlClass}>
          <Slider.Track className={sliderTrackClass}>
            <Slider.Indicator className={sliderIndicatorClass} />
            <Slider.Thumb index={0} className={sliderThumbClass} />
            <Slider.Thumb index={1} className={sliderThumbClass} />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <div className="flex pb-1">
        <div className="me-2 w-1/2 pe-2">
          <div className={inputGroupClass}>
            <input
              className={`${inputClass({ size: 'sm' })} ${groupedInputClass} rounded-e-none`}
              type="text"
              name={`${filter.name}_min`}
              value={currentValue[0]}
              onChange={(e) => handleBoundInput(0, e.currentTarget.value)} />
            <span className={addonClass}>{filter.unit}</span>
          </div>
        </div>
        <div className="w-1/2 ps-2">
          <div className={inputGroupClass}>
            <input
              className={`${inputClass({ size: 'sm' })} ${groupedInputClass} rounded-e-none`}
              type="text"
              name={`${filter.name}_max`}
              value={currentValue[1]}
              onChange={(e) => handleBoundInput(1, e.currentTarget.value)} />
            <span className={addonClass}>{filter.unit}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
