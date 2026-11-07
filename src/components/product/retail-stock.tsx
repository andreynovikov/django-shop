'use client'

import { ReactNode } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import { IconMapPin } from '@tabler/icons-react'

import { productKeys, loadProductStock } from '@/lib/queries'

// The Janome store on Avtozavodskaya and its pickpoint
const RETAIL_STORE = 295
const PICKPOINT = 296

const lineIcon = { size: 20, stroke: 1.5, className: 'me-2 -mt-1 align-middle text-muted' }

// Both parts read the same query, so the stock is fetched once
function useRetailStock(id: number) {
  const { data: stores, isSuccess } = useQuery({
    queryKey: productKeys.stock(id),
    queryFn: () => loadProductStock(id),
    select: (data) => data.filter(store => [RETAIL_STORE, PICKPOINT].includes(store.id)),
    enabled: id > 0
  })
  return {
    retailStore: stores?.find(store => store.id === RETAIL_STORE),
    pickpoint: stores?.find(store => store.id === PICKPOINT),
    isSuccess,
  }
}

// A product that is out of stock online but is in the retail store shows the store instead of the availability badge
export function RetailAvailability({ id, instock, children }: { id: number, instock: number, children: ReactNode }) {
  const { retailStore } = useRetailStock(id)

  if (instock < 1 && retailStore)
    return (
      <div className="pt-2 pb-4">
        <IconMapPin {...lineIcon} />
        <span>
          Товар есть в наличии в розничном магазине по адресу{" "}
          <Link className="whitespace-nowrap" href="/stores/">
            {retailStore.address}
          </Link>
        </span>
      </div>
    )

  return children
}

// Where else the product can be bought or picked up
export function RetailStock({ id, instock }: { id: number, instock: number }) {
  const { retailStore, pickpoint, isSuccess } = useRetailStock(id)

  return (
    <div className="flex flex-col gap-4 pt-2 pb-4">
      {retailStore && instock > 0 ? (
        <div>
          <IconMapPin {...lineIcon} />
          <span>
            Товар есть в наличии в розничном магазине по адресу{" "}
            <Link className="whitespace-nowrap" href="/stores/">
              {retailStore.city.name}, {retailStore.address}
            </Link>
          </span>
        </div>
      ) : !retailStore && isSuccess ? (
        <div>
          <IconMapPin {...lineIcon} />
          <span>Данного товара нет в наличии в розничном магазине</span>
        </div>
      ) : (
        null
      )}
      {pickpoint && (
        <div>
          <IconMapPin {...lineIcon} />
          <span>
            Товар есть в наличии в пункте выдачи по адресу{" "}
            {pickpoint.city.name}, {pickpoint.address}
            . Обязательно оформите заказ перед посещением.
          </span>
        </div>
      )}
    </div>
  )
}
