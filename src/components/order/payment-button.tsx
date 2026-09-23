import { MouseEvent } from 'react'
import { useRouter } from 'next/router'
import { useQuery } from "@tanstack/react-query"

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

import { apiFetch, loadOrder, orderKeys } from "@/lib/queries"

import { PAYMENT_CREDIT } from '@/components/order/status-badge'

export default function OrderPaymentButton({ orderId, iconOnly = false }: { orderId: number, iconOnly?: boolean }) {

  const router = useRouter()

  const { data: order, isSuccess } = useQuery({
    queryKey: orderKeys.detail(orderId),
    queryFn: () => loadOrder(orderId),
  })

  if (!isSuccess || process.env.NEXT_PUBLIC_ORIGIN === undefined)
    return null

  const handlePayment = async (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    try {
      const result = await apiFetch<{ location: string}>(`orders/${orderId}/pay/`, {
        body: {
          'return_url': process.env.NEXT_PUBLIC_ORIGIN + router.asPath
        }
      })
      window.location.assign(result.location) // axios didn't support redirects so API returns JSON with location
    } catch (error) {
      console.log(error)
    }
  }

  return (
    <OverlayTrigger
      placement="top"
      overlay={iconOnly ?
        <Tooltip>
          {order.payment === PAYMENT_CREDIT ? 'Оформить кредит' : 'Оплатить заказ'}
        </Tooltip> : <></>
      }
    >
      <button type="button" className={`btn btn-sm btn${iconOnly ? '-outline' : ''}-success ${iconOnly ? 'py-0 px-1' : ''}`} onClick={handlePayment}>
        {order.payment === PAYMENT_CREDIT ? (
          <>
            <i className={`ci-money-bag fs-${iconOnly ? 'sm' : 'lg'}`} />
            {!iconOnly && <span className="ms-2">Оформить кредит</span>}
          </>
        ) : (
          <>
            <i className={`ci-card fs-${iconOnly ? 'sm' : 'lg'}`} />
            {!iconOnly && <span className="ms-2">Оплатить заказ</span>}
          </>
        )}
      </button>

    </OverlayTrigger>
  )
}