import { ChangeEvent } from 'react'

import { FilterProps } from './types'

export default function BooleanFilter({ filter, filterValue, onFilterChanged }: FilterProps<'name' | 'id', boolean>) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value
    onFilterChanged(filter.name, value === '' ? null : value === 'true')
  }

  return (
    <div className="mb-2">
      <div className="form-check form-check-inline">
        <input
          className="form-check-input"
          type="radio"
          name={filter.name}
          id={`${filter.id}-1`}
          value="true"
          checked={filterValue === true}
          onChange={handleChange} />
        <label className="form-check-label" htmlFor={`${filter.id}-1`}>да</label>
      </div>
      <div className="form-check form-check-inline">
        <input
          className="form-check-input"
          type="radio"
          name={filter.name}
          id={`${filter.id}-0`}
          value="false"
          checked={filterValue === false}
          onChange={handleChange} />
        <label className="form-check-label" htmlFor={`${filter.id}-0`}>нет</label>
      </div>
      <div className={"form-check form-check-inline" + (filterValue !== null ? "" : " d-none")}>
        <input
          className="form-check-input"
          type="radio"
          name={filter.name}
          id={filter.id}
          value=""
          onChange={handleChange} />
        <label className="form-check-label" htmlFor={filter.id}>не важно</label>
      </div>
    </div>
  )
}
