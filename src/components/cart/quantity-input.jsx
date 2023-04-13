import { useEffect, useCallback, useRef } from 'react';

import debounce from '@/lib/debounce';

export default function QuantityInput({quantity, setQuantity, packOnly, packFactor, isLoading}) {
    const quantityRef = useRef();

    useEffect(() => {
        if (quantity !== undefined)
            quantityRef.current.value = quantity;
    }, [quantity]);

    const modifyValue = (diff) => {
        var v = +quantityRef.current.value;
        if (!v)
            v = 0;
        if (packOnly && packFactor !== 1)
            v += diff * packFactor;
        else
            v += diff;
        quantityRef.current.value = v;
        handleValueChange(v);
    }

    const handleValueChange = (v) => {
        if (isNaN(v))
            v = quantity !== undefined ? item.quantity : 0;
        else if (v < 0)
            v = 0
        else if (v > 10000)
            v = 10000;
        if (packOnly && packFactor !== 1)
            v = Math.floor(packFactor * Math.ceil(v / packFactor));
        debouncedUpdateQuantity(v);
    };

    const debouncedValueChange = useCallback(debounce((event) => handleValueChange(+event.target.value)), [quantity]);
    const debouncedUpdateQuantity = useCallback(debounce((v) => {
        setQuantity(v);
        quantityRef.current.value = v;
    }), [setQuantity]);

    return (
        <div className="input-group input-group-sm d-inline-flex" style={{width: '7rem'}}>
            <button
                className="btn btn-success"
                type="button"
                style={{width: '1.8rem'}}
                onClick={() => modifyValue(-1)}
                disabled={isLoading}>-</button>
            <input
                ref={quantityRef}
                type="text"
                className={"form-control text-center" + (isLoading ? " d-none" : "")}
                defaultValue={0}
                onChange={debouncedValueChange} />
            <button className={"form-control btn btn-outline-success" + (isLoading ? "" : " d-none")} type="button" disabled>
                <span className="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span>
            </button>
            <button
                className="btn btn-success"
                type="button"
                style={{width: '1.8rem'}}
                onClick={() => modifyValue(1)}
                disabled={isLoading}>+</button>
        </div>
    )
}
