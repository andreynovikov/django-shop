import React, { useState } from 'react';

export default function ChoiceFilter({filter, onFilterChanged}) {
    const [filterValue, setFilterValue] = useState(undefined);

    const handleChange = (e) => {
        let value = e.target.value;
        if (value === '')
            value = undefined;
        setFilterValue(value);
        onFilterChanged(filter.name, value);
    };

    return (
        <select className="form-select" name={filter.name} id={filter.id} onChange={handleChange}>
            { filter.choices?.map(([value, label]) => (
                <option value={value} key={value}>{ label }</option>
            ))}
        </select>
    )
}
