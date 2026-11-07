import { ChangeEvent, useCallback, useState } from 'react'

import { IconSearch } from '@tabler/icons-react'

import { checkClass, checkInputClass, checkLabelClass, inputClass } from '@/components/ui/form'

import { FilterProps } from './types'

type MultipleChoiceFilterProps = FilterProps<'name' | 'id' | 'choices', Array<string | number>>

export default function MultipleChoiceFilter({ filter, filterValue, onFilterChanged }: MultipleChoiceFilterProps) {
  const [itemsFilter, setItemsFilter] = useState('')
  const currentValue = filterValue ?? []

  const lowerItemsFilter = itemsFilter.toLowerCase()

  const filterItems = useCallback((value: string) => {
    return lowerItemsFilter === '' || value.toLowerCase().indexOf(lowerItemsFilter) > -1
  }, [lowerItemsFilter])

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    // choices of the backend are numbers, the ones of Diginetica are strings
    let value: string | number = +event.target.value
    if (isNaN(value))
      value = event.target.value
    let newValue
    if (event.target.checked)
      newValue = [value, ...currentValue]
    else
      newValue = currentValue.filter(v => v !== value)
    if (newValue.length === 0)
      onFilterChanged(filter.name, null)
    else
      onFilterChanged(filter.name, newValue)
  }

  return (
    <div>
      {(filter.choices?.length ?? 0) > 6 && (
        <div className="relative mb-2">
          <input
            className={`${inputClass({ size: 'sm' })} pe-12`}
            type="text"
            placeholder="Поиск"
            aria-label="Поиск"
            value={itemsFilter}
            onChange={(event) => setItemsFilter(event.target.value)} />
          <IconSearch size={14} stroke={1.5} className="absolute top-1/2 right-0 me-4 -translate-y-1/2" />
        </div>
      )}
      <div className="max-h-44 overflow-y-auto pe-4 [scrollbar-width:thin]">
        <ul className="pt-1">
          {filter.choices?.filter(([, label]) => filterItems(label)).map(([value, label]) => (
            <li className="mb-1 flex items-center justify-between" key={value}>
              <div className={checkClass()}>
                <input
                  className={checkInputClass()}
                  type="checkbox"
                  name={filter.name}
                  id={`${filter.id}-${value}`}
                  value={value}
                  checked={currentValue.includes(value)}
                  onChange={handleChange} />
                <label className={checkLabelClass} htmlFor={`${filter.id}-${value}`}>{label}</label>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
