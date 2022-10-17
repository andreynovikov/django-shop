import React, { useState } from 'react';

export default function SliderFilter({filter, onFilterChanged}) {
    const [filterValue, setFilterValue] = useState(filter.attrs?.min_value || 0);

    const handleChange = (e) => {
        let value = +e.target.value;
        setFilterValue(value);
        if (value === (filter.attrs?.min_value || 0))
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
            value={filterValue}
            min={filter.attrs?.min_value || 0}
            max={filter.attrs?.max_value}
            step={filter.attrs?.step || 1}
            onChange={handleChange} />
            <div className="ms-2 fs-sm">
                <span>{ filterValue }</span>
                { filter.unit && <span>&nbsp;{ filter.unit }</span> }
            </div>
        </div>
    )
}
