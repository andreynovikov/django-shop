import { useRef } from 'react'
import Link from 'next/link'

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'

import useBasket from '@/lib/basket'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { useBreakpoint } from '@/lib/breakpoint'

export default function ProductCard({ product, limitedBadges = false }) {
    const { status } = useSession()

    const cardRef = useRef()

    const breakpoint = useBreakpoint()
    const { addItem } = useBasket()
    const { favorites, favoritize, unfavoritize } = useFavorites()

    const handleCartClick = () => {
        addItem(product.id)
    }

    const handleFavoritesClick = () => {
        if (status === 'authenticated') {
            if (favorites.includes(product.id))
                unfavoritize(product.id)
            else
                favoritize(product.id)
        }
    }

    const buttonClass = breakpoint === 'xs' ? '' : '-outline'
    const productLink = product.variations ? product.variations : { pathname: '/products/[code]', query: { code: product.code } }

    return (
        <div ref={cardRef} className="card product-card">
            {product.enabled && (
                <div className="position-absolute ms-3 mt-2">
                    {(product.isnew && !limitedBadges) && <span className="position-static badge bg-info badge-shadow me-2 mb-2">Новинка</span>}
                    {(product.recomended && !limitedBadges) && <span className="position-static badge bg-warning badge-shadow me-2 mb-2">Рекомендуем</span>}
                    {product.sales && product.sales.map((notice, index) => (
                        notice && <span className="position-static badge bg-danger badge-shadow me-2 mb-2" key={index}>{notice}</span>
                    ))}
                </div>
            )}
            <OverlayTrigger
                placement="left"
                overlay={
                    <Tooltip>
                        {status === 'authenticated' ?
                            favorites.includes(product.id) ?
                                "В избранном" :
                                "Отложить" :
                            "Войдите или зарегистрируйтесь, чтобы добавлять товары в избранное"
                        }
                    </Tooltip>
                }
            >
                <button onClick={handleFavoritesClick} className={"btn-wishlist btn-sm" + (favorites.includes(product.id) ? " bg-accent text-light" : "")}>
                    <i className="ci-heart" />
                </button>
            </OverlayTrigger>
            <Link className="d-block mx-auto pt-3 overflow-hidden" href={productLink}>
                {product.thumbnail ? (
                    <img
                        src={product.thumbnail.url}
                        width={product.thumbnail.width}
                        height={product.thumbnail.height}
                        alt={`${product.title} ${product.whatisit ?? product.whatis}`} />
                ) : (
                    <NoImage />
                )}
            </Link>
            <div className="card-body py-2">
                <Link className="product-meta d-block fs-xs pb-1" href={productLink}>
                    {product.whatisit ?? product.whatis} {product.partnumber}
                </Link>
                <h3 className="product-title fs-sm">
                    <Link href={productLink}>
                        {product.title}
                    </Link>
                </h3>
                <div className="d-flex justify-content-between align-items-center">
                    <div className="product-price text-accent">
                        {product.variations && "от "}
                        <ProductPrice product={product} />
                    </div>
                    <div>
                        {product.variations ? (
                            <Link className={`btn btn${buttonClass}-secondary btn-sm d-block w-100`} href={product.variations}>
                                <i className="ci-eye fs-sm" />
                            </Link>
                        ) : product.enabled && product.instock ? (
                            <button className={`btn btn${buttonClass}-success btn-sm d-block w-100`} type="button" onClick={handleCartClick}>
                                <i className="ci-cart fs-sm" />
                            </button>
                        ) : (
                            <Link className={`btn btn${buttonClass}-secondary btn-sm d-block w-100`} href={productLink}>
                                <i className="ci-eye fs-sm" />
                            </Link>
                        )}
                    </div>
                    { /* TODO
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
                {product.shortdescr && <div className="fs-ms pb-2" dangerouslySetInnerHTML={{ __html: product.shortdescr }}></div>}
                {product.sales_notes && <div className="fs-ms text-info pb-2">{product.sales_notes}</div>}
                {/*
                <div className="d-flex mb-2">
                    { product.variations ? (
                        <Link className="btn btn-success btn-sm d-block w-100" href={product.variations}>
                            Выбрать
                        </Link>
                    ) : product.enabled && product.instock ? (
                        <button className="btn btn-success btn-sm d-block w-100" type="button" onClick={handleCartClick}>
                            <i className="ci-cart fs-sm me-1" />
                            Купить
                        </button>
                    ) : (
                        <Link className="btn btn-secondary btn-sm d-block w-100" href={{ pathname: '/products/[code]', query: { code: product.code }}}>
                            Подробное описание
                        </Link>
                    )}
                </div>
                */
                }
            </div>
        </div>
    )
}
