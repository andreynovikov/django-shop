import Link from "next/link"
import { useQuery } from "@tanstack/react-query"
import { IconTruckDelivery } from "@tabler/icons-react"

import OrderPaymentButton from "./payment-button"

import { getLastOrder, getUnpaidOrder, orderKeys } from "@/lib/queries"
import { useSession } from "@/lib/session"

export default function OrderTracking({ addDivider }: { addDivider: boolean }) {
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
    return <>
      {addDivider && (
        <div className="ms-4 inline-block w-0 border-s ps-4">&nbsp;</div>
      )}
      <OrderPaymentButton orderId={unpaidOrder.id} />
    </>

  if (lastOrder?.id)
    return <>
      {addDivider && (
        <div className="ms-4 inline-block w-0 border-s ps-4">&nbsp;</div>
      )}
      <Link className="whitespace-nowrap text-gray-700/90 hover:text-heading" href="/user/orders?track" rel="nofollow">
        <IconTruckDelivery size="1.15em" stroke={1.5} className="-mt-1 me-1.5 align-middle text-primary" />Отслеживание заказа
      </Link>
    </>

  return null
}