'use client'

import { useState, useEffect, useMemo, SubmitEvent } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { IconBasket } from '@tabler/icons-react'

import NoImage from '@/components/product/no-image'
import { STATUS_NEW } from '@/components/order/status-badge'
import { PageLoading } from '@/components/loading'

import { useSession } from '@/lib/session'
import { basketKeys, orderKeys, loadOrder, updateOrder, FormDataJson } from '@/lib/queries'
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
      <section className="col-lg-8">
        <div className="d-flex justify-content-between align-items-center pt-3 pb-2 mt-1">
          <h2 className="h6 mb-0">&nbsp;</h2>
        </div>
        {isFetching ? (
          <PageLoading />
        ) : isError ? (
          <div className="lead">Что-то пошло не так...</div>
        ) : (
          null
        )}
      </section>
    )

  return (
    <>
      <section className="col-lg-8">
        <div className="d-flex justify-content-center justify-content-lg-between align-items-center pt-0 pt-lg-3 pb-3 mt-1">
          <h2 className="h1 mb-0">№{order.id}</h2>
        </div>

        {(updated || order.status !== STATUS_NEW) ? (
          <>
            <h3>Спасибо за заказ!</h3>
            <p>
              Регистрационный номер Вашего заказа: <b>{order.id}</b>.
            </p>
            <p>
              Наш менеджер свяжется с Вами, уточнит состав заказа, согласует способ оплаты,
              стоимость и способ доставки, и договорится об удобном времени доставки.
            </p>
            <p>
              Узнать о состоянии заказа Вы можете по ссылке{" "}
              <Link href="/user/orders?track">
                &laquo;Отслеживание заказа&raquo;
              </Link>
              {" "}вверху страницы.
            </p>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label" htmlFor="order-name-input">Фамилия Имя Отчество:</label>
              <input type="text" name="name" className="form-control form-control-lg" id="order-name-input" defaultValue={order.name || user?.name} autoComplete="name" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="order-email-input">E-mail для уведомлений:</label>
              <input type="text" name="email" className="form-control form-control-lg" id="order-email-input" defaultValue={order.email || user?.email} autoComplete="email" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="order-address-input">Адрес доставки:</label>
              <input type="text" name="address" className="form-control form-control-lg" id="order-address-input"
                defaultValue={order.address || user?.address} autoComplete="postal-code address-level2 street-address" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="order-comment-input">Комментарии к заказу:</label>
              <textarea name="comment" className="form-control form-control-lg" id="order-comment-input" defaultValue={order.comment} rows={3}></textarea>
            </div>
            <hr className="mt-4 mb-3" />
            <div className="text-end">
              <button type="submit" className="btn btn-primary btn-lg"><IconBasket size={20} stroke={1.5} className="me-1 align-text-bottom" />Оформить заказ</button>
            </div>
          </form>
        )}
      </section>
      <aside className="col-lg-4 pt-4 pt-lg-0 ps-xl-5">
        <div className="bg-white rounded-3 shadow-lg p-4 ms-lg-auto">
          <div className="py-2 px-xl-2">
            <div className="mb-3">
              <h2 className="h4 text-center mb-3">Детали заказа</h2>
              {order.items.map((item, index) => (
                <div className={"d-flex align-items-center border-bottom " + (index === 0 ? "pb-3" : "py-3")} key={item.product.id}>
                  <div
                    className="d-block flex-shrink-0 position-relative"
                    style={{ width: 64, height: 64 }}>
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
                  </div>
                  <div className="ps-2">
                    <h6>
                      {item.product.title}
                    </h6>
                    <div>
                      <span className="text-accent me-2">{item.cost.toLocaleString('ru')}<small>&nbsp;руб</small></span>
                      <span className="text-muted">x {item.quantity}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <h3 className="fw-normal text-center my-4">
              {order.total.toLocaleString('ru')}<small>&nbsp;руб</small>
            </h3>
          </div>
        </div>
      </aside>
    </>
  )
}
