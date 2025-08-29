import Script from 'next/script';
import SimpleBar from 'simplebar-react';

export default function MultipleChoiceFilter({filter, filterValue, onFilterChanged}) {
    const currentValue = filterValue !== undefined  ? filterValue : [];

    const handleChange = (event) => {
        let value = +event.target.value;
        if (isNaN(value))
            value = event.target.value;
        let newValue;
        if (event.target.checked)
            newValue = [value, ...currentValue];
        else
            newValue = currentValue.filter(v => v !== value);
        if (newValue.length === 0)
            onFilterChanged(filter.name, undefined);
        else
            onFilterChanged(filter.name, newValue);
    };

    const setupFilterList = () => {
    };

    return (
        <div className="widget-filter">
            { filter.choices?.length > 6 && (
                <div className="input-group input-group-sm mb-2">
                    <input className="widget-filter-search form-control rounded-end pe-5" type="text" placeholder="Поиск" />
                    <i className="ci-search position-absolute top-50 end-0 translate-middle-y fs-sm me-3" />
                </div>
            )}
            <SimpleBar style={{maxHeight: "11rem"}} autoHide={false}>
                <ul className="widget-list widget-filter-list list-unstyled pt-1">
                    { filter.choices?.map(([value, label]) => (
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
                                <label className="form-check-label widget-filter-item-text" htmlFor={`${filter.id}-${value}`}>{ label }</label>
                            </div>
                        </li>
                    ))}
                </ul>
            </SimpleBar>
            { /* TODO: refactor to use native filtering */ }
            <Script
                id="filter-list"
                src="/js/components/filter-list.js"
                type="module"
                onReady={setupFilterList}
                onLoad={setupFilterList} />
        </div>
    )
}
