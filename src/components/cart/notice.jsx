import Link from 'next/link';
import SimpleBar from 'simplebar-react';

import useBasket from '@/lib/basket';

import 'simplebar-react/dist/simplebar.min.css';

export default function CartNotice() {
    const { basket, isEmpty, removeItem } = useBasket();

    const handleItemRemoveClick = (productId) => {
        removeItem(productId);
    };

    if (isEmpty)
        return (
            <div className="navbar-tool ms-3">
                <span className="navbar-tool-icon-box bg-secondary"><i className="navbar-tool-icon ci-cart" /></span>
                <span className="navbar-tool-text"><small>Корзина</small>пуста</span>
            </div>
        );

    return (
        <div className="navbar-tool ms-3 dropdown">
            <Link href="/cart">
                <a className="navbar-tool-icon-box bg-secondary dropdown-toggle">
                    <span className="navbar-tool-label">{ basket.quantity }</span><i className="navbar-tool-icon ci-cart" />
                </a>
            </Link>
            <Link href="/cart">
                <a className="navbar-tool-text"><small>Корзина</small>{ basket.total }<small className="d-inline">&nbsp;руб</small></a>
            </Link>
            <div className="dropdown-menu dropdown-menu-end">
                <div className="widget widget-cart px-3 pt-2 pb-3" style={{width: "25rem"}}>
                    <SimpleBar style={{height: "15rem"}}>
                        {basket.items.map((item, index) => (
                            <div key={item.product.id} className={"widget-cart-item border-bottom " + (index === 0 ? "pb-2" : "py-2")}>
                                <button className="btn-close text-danger" onClick={() => handleItemRemoveClick(item.product.id)} aria-label="Удалить">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                                <div className="d-flex align-items-center">
                                    <a className="d-block flex-shrink-0" href="'product'">
                                        { item.product.thumbnail_small ? (
                                            <img
                                                src={item.product.thumbnail_small.url}
                                                width={item.product.thumbnail_small.width}
                                                height={item.product.thumbnail_small.height}
                                                alt={`${item.product.title} ${item.product.whatis}`} />
                                        ) : (
                                            <i className="d-inline-block ci-camera text-muted" style={{width: "64px", height: "64px", fontSize: "32px", padding: "16px"}} />
                                        )}
                                    </a>
                                    <div className="ps-2">
                                        <h6 className="widget-product-title"><a href="'product'">{ item.product.title }</a></h6>
                                        <div className="widget-product-meta">
                                            <span className="text-accent me-2">{ item.cost }<small>&nbsp;руб</small></span>
                                            <span className="text-muted">x { item.quantity }</span>
                                            { item.product.instock < 1 && <span className="fs-lg ms-1"><sup><span className="badge badge-pill badge-warning">нет в наличии</span></sup></span> }
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </SimpleBar>
                    <div className="d-flex flex-wrap justify-content-between align-items-center py-3">
                        <div className="fs-sm me-2 py-2">
                            <span className="text-muted">Всего:</span>
                            <span className="text-accent fs-base ms-1">{ basket.total }<small>&nbsp;руб</small></span>
                        </div>
                        <Link href="/cart">
                            <a className="btn btn-outline-secondary btn-sm">Открыть корзину<i className="ci-arrow-right ms-1 me-n1" /></a>
                        </Link>
                    </div>
                    <button className="btn btn-primary btn-sm d-block w-100" href="checkout-details.html"><i className="ci-basket-alt me-2 fs-base align-middle" />Оформить заказ</button>
                </div>
            </div>
        </div>
    )
};
