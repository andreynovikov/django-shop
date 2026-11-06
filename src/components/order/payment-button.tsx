import { MouseEvent } from 'react'
import { useQuery } from "@tanstack/react-query"

import { IconCreditCard, IconPigMoney } from '@tabler/icons-react'

import { apiFetch, loadOrder, orderKeys } from "@/lib/queries"
import { useSite } from '@/lib/site'

import { PAYMENT_CREDIT } from '@/components/order/status-badge'
import Tooltip from '@/components/ui/tooltip'

export default function OrderPaymentButton({ orderId, iconOnly = false }: { orderId: number, iconOnly?: boolean }) {

  const { site } = useSite()

  const { data: order, isSuccess } = useQuery({
    queryKey: orderKeys.detail(orderId),
    queryFn: () => loadOrder(orderId),
  })

  if (!isSuccess || site?.url_prefix === undefined)
    return null

  const handlePayment = async (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation()
    try {
      const result = await apiFetch<{ location: string}>(`orders/${orderId}/pay/`, {
        body: {
          'return_url': site.url_prefix + window.location.pathname + window.location.search
        }
      })
      window.location.assign(result.location) // axios didn't support redirects so API returns JSON with location
    } catch (error) {
      console.log(error)
    }
  }

  const button = (
    <button type="button" className={`btn btn-sm btn${iconOnly ? '-outline' : ''}-success ${iconOnly ? 'py-0 px-1' : ''}`} onClick={handlePayment}>
      {order.payment === PAYMENT_CREDIT ? (
        <>
          <IconPigMoney size={iconOnly ? 16 : 20} stroke={1.5} className="align-text-bottom" />
          {!iconOnly && <span className="ms-2">Оформить кредит</span>}
        </>
      ) : (
        <>
          <IconCreditCard size={iconOnly ? 16 : 20} stroke={1.5} className="align-text-bottom" />
          {!iconOnly && <span className="ms-2">Оплатить заказ</span>}
        </>
      )}
    </button>
  )

  if (!iconOnly)
    return button

  return (
    <Tooltip content={order.payment === PAYMENT_CREDIT ? 'Оформить кредит' : 'Оплатить заказ'}>
      {button}
    </Tooltip>
  )
}