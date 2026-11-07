import { ChangeEvent } from 'react'

import { selectClass } from '@/components/ui/form'

import { FilterProps } from './types'

export default function ChoiceFilter({ filter, filterValue, onFilterChanged }: FilterProps<'name' | 'id' | 'choices', string | number>) {
  const currentValue = filterValue ?? ''

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    onFilterChanged(filter.name, value === '' ? null : value)
  }

  return (
    <select className={selectClass()} name={filter.name} id={filter.id} value={currentValue} onChange={handleChange}>
      {filter.choices?.map(([value, label]) => (
        <option value={value} key={value}>{label}</option>
      ))}
    </select>
  )
}
