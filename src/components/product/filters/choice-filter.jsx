export default function ChoiceFilter({ filter, filterValue, onFilterChanged }) {
  const currentValue = filterValue !== undefined ? filterValue : ''

  const handleChange = (event) => {
    let value = event.target.value
    if (value === '')
      value = undefined
    onFilterChanged(filter.name, value)
  }

  return (
    <select className="form-select" name={filter.name} id={filter.id} value={currentValue} onChange={handleChange}>
      {filter.choices?.map(([value, label]) => (
        <option value={value} key={value}>{label}</option>
      ))}
    </select>
  )
}
