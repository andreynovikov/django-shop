import Link from "next/link"
import { useQuery } from "@tanstack/react-query"

import OrderPaymentButton from "./payment-button"

import { getLastOrder, getUnpaidOrder, orderKeys } from "@/lib/queries"
import { useSession } from "@/lib/session"

export default function OrderTracking() {
  const { status } = useSession()

  const { data: unpaidOrder } = useQuery({
    queryKey: orderKeys.unpaid(),
    queryFn: () => getUnpaidOrder(),
    enabled: status === 'authenticated'
  })

  const { data: lastOrder } = useQuery({
    queryKey: orderKeys.last(),
    queryFn: () => getLastOrder(),
    enabled: status === 'authenticated' && unpaidOrder?.id === null
  })

  if (unpaidOrder?.id)
    return <OrderPaymentButton orderId={unpaidOrder.id} />

  if (lastOrder?.id)
    return <Link className="topbar-link text-nowrap" href="/user/orders?track" rel="nofollow">
      <i className="ci-delivery mt-n1" />Отслеживание заказа
    </Link>

  return null
}