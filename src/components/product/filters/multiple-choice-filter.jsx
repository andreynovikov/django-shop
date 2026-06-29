import { useCallback, useState } from 'react'

import SimpleBar from 'simplebar-react'

export default function MultipleChoiceFilter({ filter, filterValue, onFilterChanged }) {
  const [itemsFilter, setItemsFilter] = useState('')
  const currentValue = filterValue ?? []

  const lowerItemsFilter = itemsFilter.toLowerCase()

  const filterItems = useCallback((value) => {
    return lowerItemsFilter === '' || value.toLowerCase().indexOf(lowerItemsFilter) > -1
  }, [lowerItemsFilter])

  const handleChange = (event) => {
    let value = +event.target.value
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
    <div className="widget-filter">
      {filter.choices?.length > 6 && (
        <div className="input-group input-group-sm mb-2">
          <input
           className="widget-filter-search form-control rounded-end pe-5"
            type="text"
             placeholder="Поиск"
             value={itemsFilter}
             onChange={(event) => setItemsFilter(event.target.value)} />
          <i className="ci-search position-absolute top-50 end-0 translate-middle-y fs-sm me-3" />
        </div>
      )}
      <SimpleBar style={{ maxHeight: "11rem" }} autoHide={false}>
        <ul className="widget-list widget-filter-list list-unstyled pt-1">
          {/* eslint-disable-next-line @typescript-eslint/no-unused-vars */}
          {filter.choices?.filter(([_, label]) => filterItems(label)).map(([value, label]) => (
            <li className="widget-filter-item d-flex justify-content-between align-items-center mb-1" key={value}>
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  name={filter.name}
                  id={`${filter.id}-${value}`}
                  value={value}
                  checked={currentValue.includes(value)}
                  onChange={handleChange} />
                <label className="form-check-label widget-filter-item-text" htmlFor={`${filter.id}-${value}`}>{label}</label>
              </div>
            </li>
          ))}
        </ul>
      </SimpleBar>
    </div>
  )
}
