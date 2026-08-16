import { useMemo } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import { Collapsible } from '@base-ui/react/collapsible'

import { Loading } from '@/components/loading'

import { productKeys, loadProductStock } from '@/lib/queries'

export default function ProductStock({ id }) {
  const { data: stores, isSuccess, isLoading } = useQuery({
    queryKey: productKeys.stock(id),
    queryFn: () => loadProductStock(id),
    select: (data) => data.filter(store => store.id === 295),
    enabled: id > 0
  })

  if (isLoading)
    return null

  return (
    <div className="pt-2 pb-3">
      <i className="ci-location text-muted lead align-middle mt-n1 me-2" />
      {isSuccess && stores.length !== 0 ? (
        <span>
          Товар есть в наличии в розничном магазинe по адресу{" "}
          <Link className="text-nowrap" href="/stores/">
            {stores[0].address}
          </Link>
        </span>
      ) : (
        <span>Данного товара нет в наличии в розничном магазине</span>
      )}
    </div>
  )
}
