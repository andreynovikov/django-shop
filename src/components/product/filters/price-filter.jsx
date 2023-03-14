import React, { useState, useEffect, useRef } from 'react';
import Script from 'next/script';

import rangeSlider from '@/vendor/cartzilla/components/range-slider'; // NOTICE: autoexecution is manually removed from module

export default function PriceFilter({filter, filterValue, onFilterChanged}) {
    const [ready, setReady] = useState(false);

    const minValue = filter.attrs?.min_value || 0;
    const maxValue = filter.attrs?.max_value || 990000;
    const currentValue = filterValue !== undefined ? filterValue : [minValue, maxValue];

    const sliderRef = useRef();

    useEffect(() => {
        if (!ready)
            return;

        const ref = sliderRef.current;
        console.log('uislider', ref.noUiSlider);

        if (!!!ref.noUiSlider) {
            console.log('create range-slider');
            rangeSlider();
        }
        console.log('set slider handler');
        ref.noUiSlider.on('set', () => {
            const value = ref.noUiSlider.get(true);
            console.log('new value', value);
            value[0] = Math.round(value[0]);
            value[1] = Math.round(value[1]);
            if (value[0] !== currentValue[0] || value[1] !== currentValue[1])
                onFilterChanged(filter.name, value);
        });

        return () => {
            console.log('destroy slider');
            if (!!ref.noUiSlider) {
                ref.noUiSlider.off('set');
                ref.noUiSlider.destroy();
            }
        }
    }, [ready]);

    useEffect(() => {
        const value = sliderRef.current?.noUiSlider?.get(true) || [minValue, maxValue];
        value[0] = Math.round(value[0]);
        value[1] = Math.round(value[1]);
        if (value[0] !== currentValue[0] || value[1] !== currentValue[1])
            sliderRef.current?.noUiSlider?.set(currentValue);
    }, [filterValue]);

    const setupRangeSlider = () => {
        console.log('setupRangeSlider');
        setReady(true);
    };

    return (
        <div className="range-slider"
             data-start-min={minValue}
             data-start-max={maxValue}
             data-min="0"
             data-max={Math.ceil(maxValue * 1.1 / 1000) * 1000}
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
