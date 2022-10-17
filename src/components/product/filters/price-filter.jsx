import React, { useState, useEffect, useRef } from 'react';
import Script from 'next/script';

export default function PriceFilter({filter, onFilterChanged}) {
    const [filterValue, setFilterValue] = useState([-1,-1]);

    const sliderRef = useRef(null);

    const setFilters = () => {
        const value = sliderRef.current.noUiSlider.get(true);
        value[0] = Math.round(value[0]);
        value[1] = Math.round(value[1]);
        if (value[0] !== filterValue[0])
            onFilterChanged(`${filter.name}_min`, value[0]);
        if (value[1] !== filterValue[1])
            onFilterChanged(`${filter.name}_max`, value[1]);
        setFilterValue(value);
    };

    const setupRangeSlider = () => {
        console.log('setupRangeSlider');
        if (window && 'noUiSlider' in window && sliderRef.current && !!!sliderRef.current.noUiSlider) {
            console.log('import range-slider');
            import('@/vendor/cartzilla/components/range-slider').then((module) => {
                console.log('set slider handler');
                sliderRef.current.noUiSlider.on('set', () => {
                    setFilters();
                });
            });
        }
    };

    return (
        <div className="range-slider"
             data-start-min={filter.attrs?.min_value || 0}
             data-start-max={filter.attrs?.max_value || 990000}
             data-min="0"
             data-max={Math.ceil((filter.attrs?.max_value || 990000) * 1.1 / 1000) * 1000}
             data-step={filter.attrs?.step || 10}
             data-currency={filter.unit}>
            <div className="range-slider-ui" ref={sliderRef}></div>
            <div className="d-flex pb-1">
                <div className="w-50 pe-2 me-2">
                    <div className="input-group input-group-sm">
                        <input className="form-control range-slider-value-min" type="text" name={`${filter.name}_min`} />
                        <span className="input-group-text">{filter.unit}</span>
                    </div>
                </div>
                <div className="w-50 ps-2">
                    <div className="input-group input-group-sm">
                        <input className="form-control range-slider-value-max" type="text" name={`${filter.name}_max`} />
                        <span className="input-group-text">{filter.unit}</span>
                    </div>
                </div>
            </div>
            <Script
                id="nouislider"
                src="/js/nouislider.min.js"
                onReady={setupRangeSlider}
                onLoad={setupRangeSlider} />
        </div>
    )
}
