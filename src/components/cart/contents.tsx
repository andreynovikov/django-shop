'use client'

import { useEffect } from 'react'
import Link from 'next/link'

import { IconBasket, IconChevronLeft, IconShoppingCart } from '@tabler/icons-react'

import LoginForm from '@/components/user/login-form'
import { buttonClass } from '@/components/ui/button'
import CartItem from '@/components/cart/item'
import { PageLoading, ButtonLoading } from '@/components/loading'

import useBasket from '@/lib/basket'
import { useCreateOrder } from '@/lib/order'
import { useSession } from '@/lib/session'
import { useLastCatalog } from '@/lib/catalog/hooks'

// The header row over the dark page header: a title on the left, a link back to the catalog on the right
const headerClass = 'mt-1 flex items-center justify-between pt-4 pb-2 sm:pb-12'
const backLinkClass = `${buttonClass({ variant: 'outline-primary', size: 'sm' })} ps-2`

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
      <section className="min-w-0 lg:col-span-2">
        <div className={headerClass}>
          <h2 className="mb-0 text-h6 text-white">
            {isLoading ? "Загружается..." : isEmpty ? "Нет товаров" : ""}
          </h2>
          <Link className={backLinkClass} href={lastPage}>
            <IconChevronLeft size={16} stroke={1.5} className="me-2" />Продолжить покупки
          </Link>
        </div>
        {isLoading ? (
          <PageLoading />
        ) : isEmpty ? (
          <div className="flex items-center">
            <IconShoppingCart size={100} stroke={1} className="m-[50px] block shrink-0 text-muted" />
            <div className="text-xl font-light">Положите в корзину товар для оформления заказа</div>
          </div>
        ) : (
          <div className="text-xl font-light">Что-то пошло не так...</div>
        )}
      </section>
    )

  return (
    <>
      <section className="min-w-0 lg:col-span-2">
        <div className={headerClass}>
          <h2 className="mb-0 text-h6 text-white">Товары</h2>
          <Link className={backLinkClass} href={lastPage}>
            <IconChevronLeft size={16} stroke={1.5} className="me-2" />Продолжить покупки
          </Link>
        </div>
        {basket.items.map((item, index) => (
          <CartItem key={item.product.id} item={item} first={index === 0} last={index === basket.items.length - 1} removeItem={removeItem} setQuantity={setQuantity} />
        ))}
      </section>
      <aside className="pt-6 lg:pt-0 xl:ps-8">
        <div className="rounded-lg bg-white p-6 shadow-lg">
          <div className="py-2 xl:px-2">
            <div className="mb-6 border-b pb-4 text-center">
              <h2 className="mb-4 pb-1 text-h5">Итого</h2>
              <h3 className="mb-0 text-h3 font-normal">{basket.total.toLocaleString('ru')}<small>&nbsp;руб</small></h3>
              <div className="text-sm text-muted">без учета стоимости доставки</div>
            </div>

            {status === 'authenticated' ? (
              <>
                <div className="mb-2">Добро пожаловать, {user?.name || "уважаемый покупатель"}!</div>
                <button className={`${buttonClass({ block: true, shadow: true })} mt-6`} type="button" onClick={handleCreateOrder} disabled={isPending}>
                  <IconBasket size={18} stroke={1.5} className="me-2" />Оформить заказ
                  {isPending && <ButtonLoading />}
                </button>
              </>
            ) : (
              <LoginForm embedded="cart" ctx="order" />
            )}

            {status === 'authenticated' && (
              <div className="mt-4">
                <a className="text-sm text-primary hover:text-link-hover" onClick={() => signOut()}>Оформить заказ от другого имени</a>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
