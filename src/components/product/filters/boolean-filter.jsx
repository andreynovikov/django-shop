import React, { useState } from 'react';

export default function BooleanFilter({filter, onFilterChanged}) {
    const [filterValue, setFilterValue] = useState(undefined);

    const handleChange = (e) => {
        let value = e.target.value;
        if (value === '')
            value = undefined;
        setFilterValue(value);
        onFilterChanged(filter.name, value);
    };

    return (
        <div className="mb-2">
            <div className="form-check form-check-inline">
                <input className="form-check-input" type="radio" name={filter.name} id={`${filter.id}-1`} value="1" onChange={handleChange} />
                <label className="form-check-label" htmlFor={`${filter.id}-1`}>да</label>
            </div>
            <div className="form-check form-check-inline">
                <input className="form-check-input" type="radio" name={filter.name} id={`${filter.id}-0`} value="0" onChange={handleChange} />
                <label className="form-check-label" htmlFor={`${filter.id}-0`}>нет</label>
            </div>
            <div className={"form-check form-check-inline" + (filterValue !== undefined ? "" : " d-none")}>
                <input className="form-check-input" type="radio" name={filter.name} id={filter.id} value="" onChange={handleChange} />
                <label className="form-check-label" htmlFor={filter.id}>не важно</label>
            </div>
        </div>
    )
}
