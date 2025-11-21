import Link from "next/link"
import { useQuery } from "@tanstack/react-query"

import OrderPaymentButton from "./payment-button"

import { getLastOrder, orderKeys } from "@/lib/queries"
import { useSession } from "@/lib/session"

export default function OrderTracking() {
  const { status } = useSession()

  const { data: unpaidOrder } = useQuery({
    queryKey: orderKeys.unpaid(),
    queryFn: () => getLastOrder(),
    enabled: status === 'authenticated'
  })

  if (unpaidOrder?.id !== undefined)
    return <OrderPaymentButton orderId={unpaidOrder.id} />

  return <Link className="topbar-link text-nowrap" href="/user/orders?track" rel="nofollow">
    <i className="ci-delivery mt-n1" />Отслеживание заказа
  </Link>
}