'use client'

import { useEffect } from 'react'
import Link from 'next/link'

import { IconArrowLeft, IconBasket, IconShoppingCart } from '@tabler/icons-react'

import LoginForm from '@/components/user/login-form'
import CartItem from '@/components/cart/item'
import { PageLoading, ButtonLoading } from '@/components/loading'
import { buttonClass } from '@/components/ui/button'

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
      <section className="lg:col-span-2">
        <div className="mt-1 flex items-center justify-between py-4">
          <h2 className="leading-none font-light">
            {isLoading ? "Загружается..." : isEmpty ? "Нет товаров" : ""}
          </h2>
          <Link className={`${buttonClass({ variant: 'outline-primary', size: 'sm' })} ps-2`} href={lastPage}>
            <IconArrowLeft size={20} stroke={1.5} className="me-1" />Продолжить покупки
          </Link>
        </div>
        {isLoading ? (
          <PageLoading />
        ) : isEmpty ? (
          <div className="flex items-center">
            <IconShoppingCart className="block shrink-0 text-muted" style={noCartStyle} stroke={1} />
            <div className="text-xl font-light">Положите в корзину товар для оформления заказа</div>
          </div>
        ) : (
          <div className="text-xl font-light">Что-то пошло не так...</div>
        )}
      </section>
    )

  return (
    <>
      <section className="lg:col-span-2">
        <div className="mt-1 flex items-center justify-between py-4">
          <h2 className="leading-none font-light">Товары</h2>
          <Link className={`${buttonClass({ variant: 'outline-primary', size: 'sm' })} ps-2`} href={lastPage}>
            <IconArrowLeft size={20} stroke={1.5} className="me-1" />Продолжить покупки
          </Link>
        </div>
        {basket.items.map((item, index) => (
          <CartItem key={item.product.id} item={item} first={index === 0} last={index === basket.items.length - 1} removeItem={removeItem} setQuantity={setQuantity} />
        ))}
      </section>
      <aside className="pt-6 lg:pt-0 xl:ps-12">
        <div className="rounded-lg bg-white p-6 shadow-lg">
          <div className="py-2 xl:px-2">
            <div className="mb-6 border-b pb-4 text-center">
              <h2 className="mb-4 pb-1 text-lg leading-none font-light">Итого</h2>
              <h3 className="text-2xl leading-none">{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small></h3>
              <div className="text-xs text-muted">без учета стоимости доставки</div>
            </div>

            {status === 'authenticated' ? (
              <>
                <div className="mb-2">Добро пожаловать, {user?.name || "уважаемый покупатель"}!</div>
                <button className={`${buttonClass({ block: true })} mt-6`} type="button" onClick={handleCreateOrder} disabled={isPending}>
                  <IconBasket size={20} stroke={1.5} className="me-1" />Оформить заказ
                  {isPending && <ButtonLoading />}
                </button>
              </>
            ) : (
              <LoginForm embedded="cart" ctx="order" />
            )}

            {status === 'authenticated' && (
              <div className="mt-4">
                <a className="text-xs" onClick={() => signOut()} style={{ cursor: 'pointer' }}>Оформить заказ от другого имени</a>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
