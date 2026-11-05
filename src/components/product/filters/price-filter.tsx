import { Slider } from '@base-ui/react/slider'
import styles from './slider-filter.module.scss'

import { FilterProps } from './types'

export default function PriceFilter({ filter, filterValue, onFilterChanged }: FilterProps<'name' | 'unit' | 'attrs', number[]>) {
  const minValue = filter.attrs?.min_value ?? 0
  const maxValue = filter.attrs?.max_value ?? 2000000
  const currentValue = filterValue ?? [minValue, maxValue]

  const handleValueChange = (value: readonly number[]) => {
    // TODO: do not allow negative ranges
    const range = [Math.round(value[0]), Math.round(value[1])]
    if (range[0] !== currentValue[0] || range[1] !== currentValue[1])
      onFilterChanged(filter.name, range)
  }

  return (
    <div>
      <Slider.Root
        thumbAlignment="edge"
        value={currentValue}
        onValueChange={handleValueChange}
        min={0}
        max={maxValue /*Math.ceil(maxValue * 1.1 / 1000) * 1000*/}
        step={filter.attrs?.step || 10}
      >
        <Slider.Control className={styles.Control}>
          <Slider.Track className={styles.Track}>
            <Slider.Indicator className={styles.Indicator} />
            <Slider.Thumb index={0} className={styles.Thumb} />
            <Slider.Thumb index={1} className={styles.Thumb} />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <div className="d-flex pb-1">
        <div className="w-50 pe-2 me-2">
          <div className="input-group input-group-sm">
            <input
              className="form-control"
              type="text"
              name={`${filter.name}_min`}
              value={currentValue[0]}
              onChange={(e) => handleValueChange([Number(e.currentTarget.value), currentValue[1]])} />
            <span className="input-group-text">{filter.unit}</span>
          </div>
        </div>
        <div className="w-50 ps-2">
          <div className="input-group input-group-sm">
            <input
              className="form-control"
              type="text"
              name={`${filter.name}_max`}
              value={currentValue[1]}
              onChange={(e) => handleValueChange([currentValue[0], Number(e.currentTarget.value)])} />
            <span className="input-group-text">{filter.unit}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
