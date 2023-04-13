import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleXmark } from '@fortawesome/free-regular-svg-icons';

import NoImage from '@/components/product/no-image';
import QuantityInput from '@/components/cart/quantity-input';

export default function CartItem({item, first, last, removeItem, setQuantity, isLoading}) {
    const updateQuantity = (v) => {
        if (v != item.quantity)
            setQuantity(item.product.id, v);
    };

    return (
        <div className={"d-sm-flex justify-content-between align-items-center my-2 " + (first ? "pb-3" : "py-3") + (!last && " border-bottom")}>
            <div className="d-block d-sm-flex align-items-center text-center text-sm-start">
                { item.product.thumbnail ? (
                    <img
                        src={item.product.thumbnail.url}
                        width={item.product.thumbnail.width}
                        height={item.product.thumbnail.height}
                        alt={`${item.product.title} ${item.product.whatis}`} />
                ) : (
                    <NoImage className="d-inline-block text-muted" />
                )}
                <div className="pt-2">
                    <h3 className="product-title fs-base mb-2">
                        { item.product.title }
                    </h3>
                    <div className="fs-sm"><span className="text-muted me-2">Цена:</span>{ item.product.price.toLocaleString('ru') }<small>&nbsp;руб</small></div>
                    { item.discount > 0 && <div className="fs-sm"><span className="text-muted me-2">Скидка:</span>{ item.discount_text }</div> }
                    <div className="fs-lg text-accent pt-2"><span>{ item.price.toLocaleString('ru') }</span><small>&nbsp;руб</small></div>
                </div>
            </div>
            <div className="pt-2 pt-sm-0 ps-sm-3 mx-auto mx-sm-0 text-center text-sm-start" style={{maxWidth: "9rem"}}>
                <label className="form-label" htmlFor="quantity">Количество</label>
                <QuantityInput
                    quantity={item !== null ? item.quantity : undefined}
                    setQuantity={updateQuantity}
                    packOnly={item.product.ws_pack_only}
                    packFactor={item.product.pack_factor}
                    isLoading={isLoading} />
                <button className="btn btn-link px-0 text-danger" type="button" onClick={() => removeItem(item.product.id)}>
                    <FontAwesomeIcon icon={faCircleXmark} className="me-1" />
                    Удалить
                </button>
            </div>
        </div>
    )
};
