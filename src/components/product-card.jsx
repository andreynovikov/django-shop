import React, { useState, useEffect, useRef } from 'react';
import Script from 'next/script';
import { useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import useBasket from '@/lib/basket';
import useFavorites from '@/lib/favorites';
import { withSession, productKeys, getProductPrice } from '@/lib/queries';

const noImageStyle = {
    width: '200px',
    height: '200px',
    fontSize: '100px',
    padding: '50px'
}

export default function ProductCard({product, limitedBadges}) {
    const [cost, setCost] = useState(product.cost);
    const { data: session, status } = useSession();

    const cardRef = useRef();

    const { addItem } = useBasket();
    const { favorites, favoritize, unfavoritize } = useFavorites();

    const { data: userPrice } = useQuery(
        productKeys.price(product.id),
        () => withSession(session, getProductPrice, product.id),
        {
            enabled: status === 'authenticated',
            onError: (error) => {
                console.log(error);
            }
        }
    );

    useEffect(() => {
        setCost(userPrice ? userPrice.cost : product.cost);
    }, [userPrice]);

    const initializeBootstrap = () => {
        if (window && 'bootstrap' in window && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(cardRef.current.querySelectorAll('[data-bs-toggle="tooltip"]'));
            const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
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
            <a className="d-block mx-auto pt-3 overflow-hidden" href="#">
                { product.thumbnail ? (
                    <img src={product.thumbnail.url} width={product.thumbnail.width} height={product.thumbnail.height} alt={`${product.title} ${product.whatis}`} />
                ) : (
                    <i className="d-inline-block ci-camera text-muted" style={ noImageStyle } />
                )}
            </a>
            <div className="card-body py-2">
                <a className="product-meta d-block fs-xs pb-1" href="#">{ product.whatis } { product.partnumber }</a>
                <h3 className="product-title fs-sm"><a href="#">{ product.title }</a></h3>
                <div className="d-flex justify-content-between">
                    { product.enabled ? (
                        cost > 0 && (
                            <div className="product-price">
	                            <span className="text-accent">{ cost.toLocaleString('ru') }<small>&nbsp;руб</small></span>
                                { cost != product.price && <>{' '}<del className="fs-sm text-muted">{ product.price.toLocaleString('ru') }<small>&nbsp;руб</small></del></> }
                            </div>
                        )
                    ) : (
                        <span className="text-accent"><small>товар снят с продажи</small></span>
                    )}
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
                            <i className="ci-cart fs-sm me-1"></i>
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
