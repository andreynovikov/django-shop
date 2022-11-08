import React, { useRef } from 'react';
import Link from 'next/link';
import Script from 'next/script';

import ProductPrice from '@/components/product/price';

import useBasket from '@/lib/basket';
import useFavorites from '@/lib/favorites';
import { useSession } from '@/lib/session';

const noImageStyle = {
    width: '200px',
    height: '200px',
    fontSize: '100px',
    padding: '50px'
}

export default function ProductCard({product, limitedBadges}) {
    const { status } = useSession();

    const cardRef = useRef();

    const { addItem } = useBasket();
    const { favorites, favoritize, unfavoritize } = useFavorites();

    const initializeBootstrap = () => {
        if (window && 'bootstrap' in window && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(cardRef.current.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    };

    const handlePrimaryClick = () => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    const handleFavoritesClick = (e) => {
        const tooltip = bootstrap.Tooltip.getInstance(e.currentTarget);
        if (tooltip)
            tooltip.hide();
        if (status === 'authenticated') {
            if (favorites.includes(product.id))
                unfavoritize(product.id);
            else
                favoritize(product.id);
        }
    }

    return (
        <div ref={cardRef} className="card product-card">
            <Script id="bootstrap" src="/js/bootstrap.bundle.js" onReady={initializeBootstrap} onLoad={initializeBootstrap} />
            { product.enabled && (
                <span className="badge">
                    { (product.isnew && !limitedBadges) && <span className="sw-badge bg-info badge-shadow">Новинка</span> }
                    { (product.recomended && !limitedBadges) && <span className="sw-badge bg-warning badge-shadow">Рекомендуем</span> }
                    { product.sales && product.sales.map((notice, index) => (
                        notice && <span className="sw-badge bg-danger badge-shadow" key={index}>{notice}</span>
                    ))}
                </span>
            )}
            <a role="button"
               tabIndex="0"
               onClick={handleFavoritesClick}
               className={"btn-wishlist btn-sm" + (favorites.includes(product.id) ? " bg-accent text-light" : "")}
               data-bs-toggle="tooltip"
               data-bs-placement="left"
               title={status === 'authenticated' ? favorites.includes(product.id) ? "В избранном" : "Отложить" : "Войдите или зарегистрируйтесь, чтобы добавлять товары в избранное"}>
                <i className="ci-heart" />
            </a>
            <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                <a className="d-block mx-auto pt-3 overflow-hidden">
                    { product.thumbnail ? (
                        <img
                            src={product.thumbnail.url}
                            width={product.thumbnail.width}
                            height={product.thumbnail.height}
                            alt={`${product.title} ${product.whatis}`} />
                    ) : (
                        <i className="d-inline-block ci-camera text-muted" style={ noImageStyle } />
                    )}
                </a>
            </Link>
            <div className="card-body py-2">
                <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                    <a className="product-meta d-block fs-xs pb-1">{ product.whatis } { product.partnumber }</a>
                </Link>
                <h3 className="product-title fs-sm">
                    <Link href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                        <a>{ product.title }</a>
                    </Link>
                </h3>
                <div className="d-flex justify-content-between">
                    <div className="product-price text-accent"><ProductPrice product={product} /></div>
                    { /*
                    <div className="star-rating">
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star"></i>
                        <i className="star-rating-icon ci-star"></i>
                    </div>
                      */
                    }
                </div>
            </div>
            <div className="card-body card-body-hidden">
                { product.shortdescr && <div className="fs-ms pb-2" dangerouslySetInnerHTML={{__html: product.shortdescr }}></div> }
                { product.sales_notes && <div className="fs-ms text-info pb-2">{ product.sales_notes }</div> }
                <div className="d-flex mb-2">
                    { product.enabled && product.instock ? (
                        <button className="btn btn-primary btn-sm d-block w-100" type="button" onClick={handlePrimaryClick}>
                            <i className="ci-cart fs-sm me-1" />
                            { product.variations ? "Выбрать" : "Купить" }
                        </button>
                    ) : (
                        <a className="btn btn-secondary btn-sm d-block w-100" href="% url 'product' product.code %">Подробное описание</a>
                    )}
                </div>
                <div className="text-center">
                    <a className="nav-link-style fs-ms" href="#" data-bs-toggle="modal">
                        <i className="ci-eye align-middle me-1"></i>
                        Быстрый просмотр
                    </a>
                </div>
            </div>
        </div>
    )
}
