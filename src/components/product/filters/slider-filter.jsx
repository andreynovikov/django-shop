import { Slider } from '@base-ui/react/slider'
import styles from './slider-filter.module.scss'

export default function SliderFilter({ filter, filterValue, onFilterChanged }) {
  const minValue = filter.attrs?.min_value || 0
  const currentValue = filterValue ?? minValue

  const handleValueChange = (value) => {
    if (value === minValue)
      onFilterChanged(filter.name, null)
    else
      onFilterChanged(filter.name, value)
  }

  return (
    <div className="d-flex align-items-center">
      <Slider.Root
        thumbAlignment="edge"
        value={currentValue}
        onValueChange={handleValueChange}
        min={minValue}
        max={filter.attrs?.max_value}
        step={filter.attrs?.step || 1}
        className="flex-grow-1"
      >
        <Slider.Control className={styles.Control}>
          <Slider.Track className={styles.Track}>
            <Slider.Indicator className={styles.Indicator} />
            <Slider.Thumb className={styles.Thumb} />
          </Slider.Track>
        </Slider.Control>
      </Slider.Root>
      <div className="ms-2 fs-sm">
        <span>{currentValue}</span>
        {filter.unit && <span>&nbsp;{filter.unit}</span>}
      </div>
    </div>
  )
}
