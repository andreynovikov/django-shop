'use client'

import { useEffect } from 'react'
import Link from 'next/link'

import { IconArrowLeft, IconBasket, IconShoppingCart } from '@tabler/icons-react'

import LoginForm from '@/components/user/login-form'
import CartItem from '@/components/cart/item'
import { PageLoading, ButtonLoading } from '@/components/loading'

import useBasket from '@/lib/basket'
import { useCreateOrder } from '@/lib/order'
import { useSession } from '@/lib/session'
import { useLastCatalog } from '@/lib/catalog/hooks'

const noCartStyle = {
  width: '200px',
  height: '200px',
  padding: '50px'
}

export default function CartContents() {
  const { user, registered, status, invalidate, signOut } = useSession()
  const { basket, isEmpty, isLoading, isSuccess, removeItem, setQuantity } = useBasket()

  const { mutate, isPending } = useCreateOrder()

  // a new buyer, registered by the login form without a code, orders right away
  useEffect(() => {
    if (status === 'authenticated' && registered) {
      mutate()
      invalidate()
    }
  }, [invalidate, mutate, registered, status])

  const handleCreateOrder = () => {
    mutate()
  }

  const lastPage = useLastCatalog()

  if (!isSuccess || isEmpty)
    return (
      <section className="col-lg-8">
        <div className="d-flex justify-content-between align-items-center pt-3 pb-3 mt-1">
          <h2 className="h6 mb-0">
            {isLoading ? "Загружается..." : isEmpty ? "Нет товаров" : ""}
          </h2>
          <Link className="btn btn-outline-primary btn-sm ps-2" href={lastPage}>
            <IconArrowLeft size={20} stroke={1.5} className="me-1 align-text-bottom" />Продолжить покупки
          </Link>
        </div>
        {isLoading ? (
          <PageLoading />
        ) : isEmpty ? (
          <div className="d-flex flex-row align-items-center">
            <IconShoppingCart className="d-block flex-shrink-0 text-muted" style={noCartStyle} stroke={1} />
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
        <div className="d-flex justify-content-between align-items-center pt-3 pb-3 mt-1">
          <h2 className="h6 mb-0">Товары</h2>
          <Link className="btn btn-outline-primary btn-sm ps-2" href={lastPage}>
            <IconArrowLeft size={20} stroke={1.5} className="me-1 align-text-bottom" />Продолжить покупки
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
                <button className="btn btn-primary btn-shadow d-block w-100 mt-4" type="button" onClick={handleCreateOrder} disabled={isPending}>
                  <IconBasket size={20} stroke={1.5} className="me-1 align-text-bottom" />Оформить заказ
                  {isPending && <ButtonLoading />}
                </button>
              </>
            ) : (
              <LoginForm embedded="cart" ctx="order" />
            )}

            {status === 'authenticated' && (
              <div className="mt-3">
                <a className="fs-sm link-primary" onClick={() => signOut()} style={{ cursor: 'pointer' }}>Оформить заказ от другого имени</a>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
