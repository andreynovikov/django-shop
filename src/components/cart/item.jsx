import { useCallback } from 'react';

import debounce from '@/lib/debounce';

export default function CartItem({item, first, last, removeItem, setQuantity}) {
    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            event.preventDefault();
            event.target.blur();
        }
    };

    const handleValueChange = (e) => {
        var v = e.target.value;
        if (!v)
            v = item.quantity
        else if (v < 1)
            v = 1
        else if (v > 10000)
            v = 10000;
        if (v != e.target.value)
            e.target.value = v;
        if (v != item.quantity)
            setQuantity(item.product.id, v);
    };

    const debouncedValueChange = useCallback(debounce(handleValueChange), []);

    return (
        <div className={"d-sm-flex justify-content-between align-items-center my-2 " + (first ? "pb-3" : "py-3") + (!last && " border-bottom")}>
            <div className="d-block d-sm-flex align-items-center text-center text-sm-start">
                <a className="d-inline-block flex-shrink-0 mx-auto me-sm-4" href="'product' item.product.code">
                    { item.product.thumbnail ? (
                        <img
                            src={item.product.thumbnail.url}
                            width={item.product.thumbnail.width}
                            height={item.product.thumbnail.height}
                            alt={`${item.product.title} ${item.product.whatis}`} />
                    ) : (
                        <i className="d-inline-block ci-camera text-muted" style={{width: "160px", height: "160px", fontSize: "80px", padding: "40px"}} />
                    )}
                </a>
                <div className="pt-2">
                    <h3 className="product-title fs-base mb-2">
                        <a href="'product' item.product.code">{ item.product.title }</a>
                    </h3>
                    <div className="fs-sm"><span className="text-muted me-2">Цена:</span>{ item.product.price.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                    { item.discount > 0 && <div className="fs-sm"><span className="text-muted me-2">Скидка:</span>{ item.discount_text }</div> }
                    <div className="fs-lg text-accent pt-2"><span>{ item.price.toLocaleString('ru') }</span><small>&nbsp;руб</small></div>
                </div>
            </div>
            <div className="pt-2 pt-sm-0 ps-sm-3 mx-auto mx-sm-0 text-center text-sm-start" style={{maxWidth: "9rem"}}>
                <label className="form-label" htmlFor="quantity">Количество</label>
                <input
                    className="form-control"
                    type="number"
                    min="1"
                    max="10000"
                    defaultValue={ item.quantity }
                    onChange={debouncedValueChange}
                    onBlur={handleValueChange}
                    onKeyDown={handleKeyDown} />
                <button className="btn btn-link px-0 text-danger" type="button" onClick={() => removeItem(item.product.id)}>
                    <i className="ci-close-circle me-2" />Удалить
                </button>
            </div>
        </div>
    )
};

