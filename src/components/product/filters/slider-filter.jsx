export default function SliderFilter({filter, filterValue, onFilterChanged}) {
    const minValue = filter.attrs?.min_value || 0;
    const currentValue = filterValue !== undefined ? filterValue : minValue;

    const handleChange = (event) => {
        let value = +event.target.value;
        if (value === minValue)
            onFilterChanged(filter.name, undefined);
        else
            onFilterChanged(filter.name, value);
    };

    return (
        <div className="d-flex align-items-center">
        <input
            className="form-range"
            type="range"
            name={filter.name}
            id={filter.id}
            value={currentValue}
            min={minValue}
            max={filter.attrs?.max_value}
            step={filter.attrs?.step || 1}
            onChange={handleChange} />
            <div className="ms-2 fs-sm">
                <span>{ currentValue }</span>
                { filter.unit && <span>&nbsp;{ filter.unit }</span> }
            </div>
        </div>
    )
}
