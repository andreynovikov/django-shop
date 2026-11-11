'use client'

import { useState, useEffect, useMemo, SubmitEvent } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { IconBasket } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import ProductLink from '@/components/product/product-link'
import { buttonClass } from '@/components/ui/button'
import { inputClass, labelClass } from '@/components/ui/form'
import { widgetProductMetaClass, widgetProductTitleClass, widgetTitleClass } from '@/components/ui/widget'
import { STATUS_NEW } from '@/components/order/status-badge'
import { ButtonLoading, PageLoading } from '@/components/loading'

import { useSession } from '@/lib/session'
import { basketKeys, orderKeys, userKeys, loadOrder, updateOrder, FormDataJson } from '@/lib/queries'
import { User } from '@/lib/types'

export default function OrderConfirmation() {
  const [updated, setUpdated] = useState(false)

  const router = useRouter()

  const { user: sessionUser, status } = useSession({
    onUnauthenticated: () => {
      router.push('/cart')
    }
  })
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const queryClient = useQueryClient()

  useEffect(() => {
    // we do it here otherwise cart page flickers on order registration
    queryClient.invalidateQueries({ queryKey: basketKeys.all })
  }, [queryClient])

  const orderId = useMemo(() => {
    if (status !== 'authenticated')
      return 0 // wait for authentication

    const id = Number(sessionStorage.getItem('lastOrder')) // TODO: clean after some extent
    return id > 0 ? id : undefined
  }, [status])

  useEffect(() => {
    if (orderId === undefined)
      router.push('/user/orders') // we know nothing about last order
  }, [orderId, router])

  const { data: order, isSuccess, isFetching, isError } = useQuery({
    queryKey: orderKeys.detail(orderId ?? 0),
    queryFn: () => loadOrder(orderId!),
    enabled: !!orderId && status === 'authenticated',
    refetchInterval: (query) => query.state.data?.status === STATUS_NEW ? 60 * 1000 : false // check for updates every minute
  })

  const updateOrderMutation = useMutation({
    mutationFn: ({ id, data }: { id: number, data: FormDataJson }) => updateOrder(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: orderKeys.detail(id) })
      // a buyer without an address gets the order's one, to confirm
      queryClient.invalidateQueries({ queryKey: userKeys.details() })
    }
  })

  const handleSubmit = (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault()
    e.stopPropagation()

    const data = Object.fromEntries(new FormData(e.currentTarget).entries())
    updateOrderMutation.mutate({ id: order!.id, data }, {
      onSuccess: () => {
        setUpdated(true)
      },
      onError: (error) => {
        console.error(error)
      }
    })
  }

  if (!isSuccess)
    return (
      <section className="min-w-0 lg:col-span-2">
        <div className="mt-1 flex items-center justify-between pt-4 pb-2 sm:pb-overlap">
          <h2 className="mb-0 text-h6 text-overlap">&nbsp;</h2>
        </div>
        {isFetching ? (
          <PageLoading />
        ) : isError ? (
          <div className="text-xl font-light">Что-то пошло не так...</div>
        ) : (
          null
        )}
      </section>
    )

  return (
    <>
      <section className="min-w-0 lg:col-span-2">
        <div className="mt-1 mb-4 flex items-center justify-center pt-0 pb-overlap lg:mb-0 lg:justify-between lg:pt-4">
          <h2 className="mb-0 text-h1 text-overlap">№{order.id}</h2>
        </div>

        {(updated || order.status !== STATUS_NEW) ? (
          <>
            <h3 className="mb-3 text-h3">Спасибо за заказ!</h3>
            <p className="mb-4">
              Регистрационный номер Вашего заказа: <b>{order.id}</b>.
            </p>
            <p className="mb-4">
              Наш менеджер свяжется с Вами, уточнит состав заказа, согласует способ оплаты,
              стоимость и способ доставки, и договорится об удобном времени доставки.
            </p>
            {order.email && user && (
              user.email.toLowerCase() !== order.email.toLowerCase() ? (
                <p className="mb-4">
                  Уведомления о заказе приходят только на подтверждённый адрес эл.почты
                  из <Link href="/user/profile/">профиля</Link>.
                </p>
              ) : !user.email_verified && (
                <p className="mb-4">
                  Мы отправили на {order.email} письмо со ссылкой для подтверждения адреса.
                  Уведомления о заказе придут на него, когда Вы его подтвердите.
                </p>
              )
            )}
            <p className="mb-4">
              Узнать о состоянии заказа Вы можете по ссылке{" "}
              <Link href="/user/orders?track">
                &laquo;Отслеживание заказа&raquo;
              </Link>
              {" "}вверху страницы.
            </p>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className={labelClass} htmlFor="order-name-input">Фамилия Имя Отчество:</label>
              <input type="text" name="name" className={inputClass({ size: 'lg' })} id="order-name-input" defaultValue={order.name || user?.name} autoComplete="name" />
            </div>
            <div className="mb-4">
              <label className={labelClass} htmlFor="order-email-input">E-mail для уведомлений:</label>
              <input type="text" name="email" className={inputClass({ size: 'lg' })} id="order-email-input" defaultValue={order.email || user?.email} autoComplete="email" />
            </div>
            <div className="mb-4">
              <label className={labelClass} htmlFor="order-address-input">Адрес доставки:</label>
              <input type="text" name="address" className={inputClass({ size: 'lg' })} id="order-address-input"
                defaultValue={order.address || user?.address} autoComplete="postal-code address-level2 street-address" />
            </div>
            <div className="mb-4">
              <label className={labelClass} htmlFor="order-comment-input">Комментарии к заказу:</label>
              <textarea name="comment" className={inputClass({ size: 'lg' })} id="order-comment-input" defaultValue={order.comment} rows={3}></textarea>
            </div>
            <hr className="mt-6 mb-4" />
            <div className="text-end">
              <button type="submit" className={buttonClass({ size: 'lg' })} disabled={updateOrderMutation.isPending}>
                <IconBasket size={18} stroke={1.5} className="me-2" />Оформить заказ
                {updateOrderMutation.isPending && <ButtonLoading />}
              </button>
            </div>
          </form>
        )}
      </section>
      <aside className="pt-6 lg:pt-0 xl:ps-8">
        <div className="rounded-lg bg-white p-6 shadow-lg lg:ms-auto">
          <div className="py-2 xl:px-2">
            <div className="mb-4">
              <h2 className={`${widgetTitleClass} text-center`}>Детали заказа</h2>
              {order.items.map((item, index) => (
                <div className={`flex items-center border-b ${index === 0 ? "pb-4" : "py-4"}`} key={item.product.id}>
                  <ProductLink className="relative block size-16 shrink-0" code={item.product.code}>
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
                  </ProductLink>
                  <div className="ps-2">
                    <h6 className={`mb-1 ${widgetProductTitleClass}`}>
                      <ProductLink code={item.product.code}>
                        {item.product.title}
                      </ProductLink>
                    </h6>
                    <div className={widgetProductMetaClass}>
                      <span className="me-2 text-accent">{item.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
                      <span className="text-muted">x {item.quantity}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <h3 className="my-6 text-center text-h3 font-normal">
              {order.total.toLocaleString('ru')}<small>&nbsp;руб</small>
            </h3>
          </div>
        </div>
      </aside>
    </>
  )
}
