import Link from 'next/link'

import PageLayout from '@/components/layout/page'
import LoginForm from '@/components/login-form'
import CartItem from '@/components/cart/item'

import useBasket from '@/lib/basket'
import { useSession, signOut } from '@/lib/session'
import { useLastCatalog } from '@/lib/catalog'

export default function Cart() {
  const { user, status } = useSession()
  const { basket, isEmpty, isLoading, isSuccess, removeItem, setQuantity } = useBasket()
  const lastPage = useLastCatalog()

  const noCartStyle = {
    width: '200px',
    height: '200px',
    fontSize: '100px',
    padding: '50px'
  }

  if (!isSuccess || isEmpty)
    return (
      <section className="col-lg-8">
        <div className="d-flex justify-content-between align-items-center pt-3 pb-2 pb-sm-5 mt-1">
          <h2 className="h6 text-light mb-0">
            {isLoading ? "Загружается..." : isEmpty ? "Нет товаров" : ""}
          </h2>
          <Link className="btn btn-outline-primary btn-sm ps-2" href={lastPage}>
            <i className="ci-arrow-left me-2" />Продолжить покупки
          </Link>
        </div>
        {isLoading ? (
          <div className="spinner-border" style={{ width: "5rem", height: "5rem" }} role="status">
            <span className="visually-hidden">Загружается...</span>
          </div>
        ) : isEmpty ? (
          <div className="d-flex flex-row align-items-center">
            <i className="ci-cart d-block text-muted" style={noCartStyle} />
            <div className="lead">Положите в корзину товар для оформления заказа</div>
          </div>
        ) : (
          <div className="lead">Что-то пошло не так...</div>
        )}
      </section>
    )

  return (
    <>
      <section className="col-lg-8">
        <div className="d-flex justify-content-between align-items-center pt-3 pb-2 pb-sm-5 mt-1">
          <h2 className="h6 text-light mb-0">Товары</h2>
          <Link className="btn btn-outline-primary btn-sm ps-2" href={lastPage}>
            <i className="ci-arrow-left me-2" />Продолжить покупки
          </Link>
        </div>
        {basket.items.map((item, index) => (
          <CartItem key={item.product.id} item={item} first={index === 0} last={index === basket.items.length - 1} removeItem={removeItem} setQuantity={setQuantity} />
        ))}
      </section>
      <aside className="col-lg-4 pt-4 pt-lg-0 ps-xl-5">
        <div className="bg-white rounded-3 shadow-lg p-4">
          <div className="py-2 px-xl-2">
            <div className="text-center mb-4 pb-3 border-bottom">
              <h2 className="h5 mb-3 pb-1">Итого</h2>
              <h3 className="fw-normal mb-0">{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small></h3>
              <div className="fs-sm text-muted">без учета стоимости доставки</div>
            </div>

            {status === 'authenticated' ? (
              <>
                <div className="mb-2">Добро пожаловать, {user?.name || "уважаемый покупатель"}!</div>
                <Link className="btn btn-primary btn-shadow d-block w-100 mt-4" href="/confirmation">
                  <i className="fs-lg me-2 ci-basket-alt" />Оформить заказ
                </Link>
              </>
            ) : (
              <LoginForm embedded={true} ctx="order" />
            )}

            {status === 'authenticated' && (
              <div className="mt-3">
                <a className="fs-sm link-primary" onClick={signOut} style={{ cursor: 'pointer' }}>Оформить заказ от другого имени</a>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

Cart.getLayout = function getLayout(page) {
  return (
    <PageLayout title="Ваша корзина" htmlTitle="Корзина" dark overlapped hideCartNotice>
      <div className="container pb-5 mb-2 mb-md-4">
        <div className="row">
          {page}
        </div>
      </div>
    </PageLayout>
  )
}
