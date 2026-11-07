import { MouseEvent } from 'react'
import { useQuery } from "@tanstack/react-query"

import { apiFetch, loadOrder, orderKeys } from "@/lib/queries"
import { useSite } from '@/lib/site'

import { IconCreditCard, IconMoneybag } from '@tabler/icons-react'

import { PAYMENT_CREDIT } from '@/components/order/status-badge'
import { buttonClass } from '@/components/ui/button'
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

  const label = order.payment === PAYMENT_CREDIT ? 'Оформить кредит' : 'Оплатить заказ'
  const Icon = order.payment === PAYMENT_CREDIT ? IconMoneybag : IconCreditCard

  const button = (
    <button
      type="button"
      className={buttonClass({ variant: iconOnly ? 'outline-success' : 'success', size: iconOnly ? 'icon-sm' : 'sm' })}
      onClick={handlePayment}
      aria-label={iconOnly ? label : undefined}>
      <Icon size={iconOnly ? 14 : 18} stroke={1.5} />
      {!iconOnly && <span className="ms-2">{label}</span>}
    </button>
  )

  if (!iconOnly)
    return button

  return (
    <Tooltip content={label}>
      {button}
    </Tooltip>
  )
}