import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import useBasket from '@/lib/basket';
import { withSession, productKeys, getProductPrice } from '@/lib/queries';

export default function ProductCard({product}) {
    const [cost, setCost] = useState(product.cost);
    const { data: session, status } = useSession();

    const { addItem } = useBasket();

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

    const noImageStyle = {
        width: '200px',
        height: '200px',
        fontSize: '100px',
        padding: '50px'
    }

    const handlePrimaryClick = () => {
        if (product.variations) {
        } else {
            addItem(product.id);
        }
    };

    return (
        <div className="card product-card">
            <span className="badge bg-danger badge-shadow">Sale</span>
            <button className="btn-wishlist btn-sm" type="button" data-bs-toggle="tooltip" data-bs-placement="left" title="Add to wishlist">
                <i className="ci-heart"></i>
            </button>
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
                    { cost > 0 && (
                        <div className="product-price">
	                        <span className="text-accent">{ cost }<small>&nbsp;руб</small></span>
                            { cost != product.price && <>{' '}<del className="fs-sm text-muted">{ product.price }<small>&nbsp;руб</small></del></> }
                        </div>
                    )}
                    <div className="star-rating">
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star-filled active"></i>
                        <i className="star-rating-icon ci-star"></i>
                        <i className="star-rating-icon ci-star"></i>
                    </div>
                </div>
            </div>
            <div className="card-body card-body-hidden">
                <div className="d-flex mb-2">
                    { product.instock ? (
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
