import { useMemo, useRef } from 'react'
import Link from 'next/link'
import Image from 'next/image'

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

import NoImage from '@/components/product/no-image'
import ProductPrice from '@/components/product/price'

import useBasket from '@/lib/basket'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'

export default function ProductCard({ product, limitedBadges = false }) {
  const { status } = useSession()

  const cardRef = useRef()

  const { basket, addItem, isSuccess, isEmpty } = useBasket()
  const { favorites, favoritize, unfavoritize } = useFavorites()

  const basketQuantity = useMemo(() => {
    if (!isSuccess || isEmpty)
      return 0
    const items = basket.items.filter(item => item.product.id == product.id)
    if (items.length > 0)
      return items[0].quantity
    else
      return 0
  }, [basket, product, isSuccess, isEmpty])

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

  const productLink = product.variations ? product.variations : { pathname: '/products/[code]', query: { code: product.code } }

  return (
    <div ref={cardRef} className="card product-card h-100">
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
      <Link className="d-block mt-3 p-6" href={productLink}>
        <div className="m-3 p-3">
          <div className="position-relative p-3 overflow-hidden" style={{ aspectRatio: 1 }}>
            {product.image ? (
              <Image
                src={product.image}
                fill
                style={{ objectFit: "contain" }}
                sizes="(min-width: 500px) 50vw, (min-width: 768px) 33vw, 100vw"
                loading="lazy"
                alt={`${product.title} ${product.whatisit ?? product.whatis}`} />
            ) : (
              <NoImage />
            )}
          </div>
        </div>
      </Link>
      <div className="d-flex flex-column card-body py-2">
        <Link className="product-meta d-block fs-xs pb-1" href={productLink}>
          {product.whatisit ?? product.whatis} {product.partnumber}
        </Link>
        <h3 className="product-title fs-6">
          <Link href={productLink}>
            {product.title}
          </Link>
        </h3>
        <div className="mt-auto">
          {product.enabled && (
            <div>
              {(product.isnew && !limitedBadges) && <span className="small fw-bold me-2 text-info">Новинка</span>}
              {(product.recomended && !limitedBadges) && <span className="small fw-bold me-2 text-success">Рекомендуем</span>}
              {product.sales && product.sales.map((notice, index) => (
                notice && <span className="small fw-bold me-2 text-danger" key={index}>{notice}</span>
              ))}
            </div>
          )}
          <div className="d-flex justify-content-between align-items-center">
            <div className="product-price text-accent">
              {product.variations && "от "}
              <ProductPrice product={product} />
            </div>
            <div>
              {product.variations ? (
                <Link className="btn btn-secondary btn-sm d-block w-100" href={product.variations}>
                  <i className="ci-eye fs-sm" />
                </Link>
              ) : product.enabled && product.instock ? (
                <button className="btn btn-success btn-sm d-block w-100 sw-button" type="button" onClick={handleCartClick}>
                  <i className="ci-cart fs-sm" />
                  {basketQuantity > 0 && <span className="sw-button-label">{basketQuantity}</span>}
                </button>
              ) : (
                <Link className="btn btn-secondary btn-sm d-block w-100" href={productLink}>
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
