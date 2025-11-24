import Link from 'next/link'
import Image from 'next/image'
import SimpleBar from 'simplebar-react'

import NoImage from '@/components/product/no-image'

import useBasket from '@/lib/basket'

export function MobileCartNotice() {
  const { basket, isEmpty } = useBasket()

  return (
    <Link className="d-table-cell handheld-toolbar-item" href="/cart">
      <span className="handheld-toolbar-icon">
        <i className="ci-cart" />
        {!isEmpty && <span className="badge bg-primary rounded-pill ms-1">{basket.quantity}</span>}
      </span>
      <span className="handheld-toolbar-label">
        {isEmpty ? <>Корзина&nbsp;пуста</> : <>{basket.total.toLocaleString('ru')}&nbsp;руб</>}
      </span>
    </Link>
  )
}

export default function CartNotice() {
  const { basket, isEmpty, removeItem } = useBasket()

  const handleItemRemoveClick = (productId) => {
    removeItem(productId)
  }

  if (isEmpty)
    return (
      <div className="navbar-tool ms-3 d-none d-lg-flex">
        <span className="navbar-tool-icon-box bg-secondary"><i className="navbar-tool-icon ci-cart" /></span>
        <span className="navbar-tool-text"><small>Корзина</small>пуста</span>
      </div>
    )

  return (
    <div className="navbar-tool ms-3 d-none d-lg-flex dropdown">
      <Link className="navbar-tool-icon-box bg-secondary dropdown-toggle" href="/cart">
        <span className="navbar-tool-label">{basket.quantity}</span><i className="navbar-tool-icon ci-cart" />
      </Link>
      <Link className="navbar-tool-text" href="/cart">
        <small>Корзина</small>{basket.total.toLocaleString('ru')}<small className="d-inline">&nbsp;руб</small>
      </Link>
      <div className="dropdown-menu dropdown-menu-end">
        <div className="widget widget-cart px-3 pt-2 pb-3" style={{ width: "25rem" }}>
          <SimpleBar style={{ height: "15rem" }}>
            {basket.items.map((item, index) => (
              <div key={item.product.id} className={"widget-cart-item border-bottom " + (index === 0 ? "pb-2" : "py-2")}>
                <button className="btn-close text-danger" onClick={() => handleItemRemoveClick(item.product.id)} aria-label="Удалить">
                  <span aria-hidden="true">&times;</span>
                </button>
                <div className="d-flex align-items-center">
                  <Link
                    className="d-block flex-shrink-0 position-relative"
                    style={{ width: 64, height: 64 }}
                    href={{ pathname: '/products/[code]', query: { code: item.product.code } }}>
                    {item.product.image ? (
                      <Image
                        src={item.product.image}
                        fill
                        style={{ objectFit: 'contain' }}
                        sizes="64px"
                        loading="lazy"
                        alt={`${item.product.whatis ? item.product.whatis + ' ' : ''}${item.product.title}`} />
                    ) : (
                      <NoImage size={64} />
                    )}
                  </Link>
                  <div className="ps-2">
                    <h6 className="widget-product-title">
                      <Link href={{ pathname: '/products/[code]', query: { code: item.product.code } }}>
                        {item.product.title}
                      </Link>
                    </h6>
                    <div className="widget-product-meta">
                      <span className="text-accent me-2">{item.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
                      <span className="text-muted">x {item.quantity}</span>
                      {item.product.instock < 1 && <span className="fs-lg ms-1"><sup><span className="badge badge-pill badge-warning">нет в наличии</span></sup></span>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </SimpleBar>
          <div className="d-flex flex-wrap justify-content-between align-items-center py-3">
            <div className="fs-sm me-2 py-2">
              <span className="text-muted">Всего:</span>
              <span className="text-accent fs-base ms-1">{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small></span>
            </div>
            <Link className="btn btn-outline-secondary btn-sm" href="/cart">
              Открыть корзину<i className="ci-arrow-right ms-1 me-n1" />
            </Link>
          </div>
          <Link className="btn btn-primary btn-sm d-block w-100" href="/confirmation">
            <i className="ci-basket-alt me-2 fs-base align-middle" />Оформить заказ
          </Link>
        </div>
      </div>
    </div>
  )
};
