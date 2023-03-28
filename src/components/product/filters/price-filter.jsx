import React, { useState, useEffect, useRef } from 'react';
import Script from 'next/script';

export default function PriceFilter({filter, filterValue, onFilterChanged}) {
    const [ready, setReady] = useState(false);

    const minValue = filter.attrs?.min_value || 0;
    const maxValue = filter.attrs?.max_value || 990000;
    const currentValue = filterValue !== undefined ? filterValue : [minValue, maxValue];

    const sliderRef = useRef();
    const minValueRef = useRef();
    const maxValueRef = useRef();

    useEffect(() => {
        if (!ready)
            return;

        const ref = sliderRef.current;
        console.log('uislider', ref.noUiSlider);

        if (!!ref.noUiSlider)
            return;

        console.log('create range-slider');

        const step = filter.attrs?.step || 10;

        noUiSlider.create(ref, {
            start: [minValue, maxValue],
            connect: true,
            step: step,
            pips: {mode: 'count', values: 5},
            tooltips: true,
            range: {
                'min': 0,
                'max': Math.ceil(maxValue * 1.1 / 1000) * 1000
            },
            format: {
                to: function (value) {
                    return parseInt(value, 10) + ' ' + filter.unit;
                },
                from: function (value) {
                    return Number(value);
                }
            }
        });

        ref.noUiSlider.on('update', (values, handle) => {
            let value = values[handle];
            value = value.replace(/\D/g,'');
            if (handle) {
                maxValueRef.current.value = Math.round(value);
            } else {
                minValueRef.current.value = Math.round(value);
            }
        });

        ref.noUiSlider.on('set', () => {
            const value = ref.noUiSlider.get(true);
            console.log('new value', value);
            value[0] = Math.round(value[0]);
            value[1] = Math.round(value[1]);
            if (value[0] !== currentValue[0] || value[1] !== currentValue[1])
                onFilterChanged(filter.name, value);
        });

        return () => {
            console.log('destroy range-slider');
            if (!!ref.noUiSlider) {
                ref.noUiSlider.off('update');
                ref.noUiSlider.off('set');
                ref.noUiSlider.destroy();
            }
        }
    }, [ready]);

    useEffect(() => {
        if (!ready)
            return;

        console.log('set new value');
        const value = sliderRef.current?.noUiSlider?.get(true) || [minValue, maxValue];
        value[0] = Math.round(value[0]);
        value[1] = Math.round(value[1]);
        if (value[0] !== currentValue[0] || value[1] !== currentValue[1])
            sliderRef.current?.noUiSlider?.set(currentValue);
    }, [ready, filterValue]);

    const setRangeValue = (value) => {
        sliderRef.current?.noUiSlider?.set(value);
    };

    const setupRangeSlider = () => {
        console.log('setupRangeSlider');
        setReady(true);
    };

    return (
        <div className="range-slider">
            <div className="range-slider-ui" ref={sliderRef}></div>
            <div className="d-flex pb-1">
                <div className="w-50 pe-2 me-2">
                    <div className="input-group input-group-sm">
                        <input
                            className="form-control range-slider-value-min"
                            type="text"
                            name={`${filter.name}_min`}
                            onChange={(e) => setRangeValue([e.currentTarget.value, null])}
                            ref={minValueRef} />
                        <span className="input-group-text">{filter.unit}</span>
                    </div>
                </div>
                <div className="w-50 ps-2">
                    <div className="input-group input-group-sm">
                        <input
                            className="form-control range-slider-value-max"
                            type="text"
                            name={`${filter.name}_max`}
                            onChange={(e) => setRangeValue([null, e.currentTarget.value])}
                            ref={maxValueRef} />
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
