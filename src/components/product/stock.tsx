import { useMemo } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import { Collapsible } from '@base-ui/react/collapsible'
import { IconCheck } from '@tabler/icons-react'

import { Loading } from '@/components/loading'

import { productKeys, loadProductStock } from '@/lib/queries'
import { City, StoreInfo } from '@/lib/types'

export default function ProductStock({ id }: { id: number }) {
  const { data: stores, isSuccess, isLoading } = useQuery({
    queryKey: productKeys.stock(id),
    queryFn: () => loadProductStock(id),
    select: (data) => data.filter(store => store.id !== 295),
    enabled: id > 0
  })

  const storeGroups = useMemo(() => {
    if (!isSuccess)
      return []

    // Store list is sorted by city
    const { groups } = stores.reduce(({ groups, city }, store) => {
      if (store.city.id !== city) {
        groups.push({ city: store.city, stores: [] })
        city = store.city.id
      }
      groups[groups.length - 1].stores.push(store)
      return { groups, city }
    }, { groups: [] as {city: City, stores: StoreInfo[]}[], city: null as number | null })

    return groups.sort((a, b) => a.city.name.localeCompare(b.city.name))
  }, [stores, isSuccess])

  if (isLoading)
    return <Loading className="text-center" />

  if (!isSuccess || stores.length === 0)
    return <div className="py-4 font-bold text-dark">Данного товара нет в наличии в розничных магазинах</div>

  return (
    <>
      <div className="pt-2 pb-4 text-sm">Товар есть в наличии в следующих магазинах:</div>
      {storeGroups.map(({ city, stores }, index) => (
        <Collapsible.Root className={`border-b ${index === 0 ? "pb-2" : "py-2"}`} key={city.id}>
          <Collapsible.Trigger className="block cursor-pointer p-0 text-sm text-muted transition-colors hover:text-gray-700" nativeButton={false} render={<div />}>
            {city.name}
          </Collapsible.Trigger>
          <Collapsible.Panel>
            {stores.map((store) => (
              <Link className="block pt-1 text-xs" href={`/stores/${store.id}/`} key={store.id}>
                <IconCheck size={12} stroke={2} className="me-1 text-muted" />
                {store.address}
              </Link>
            ))}
          </Collapsible.Panel>
        </Collapsible.Root>
      ))}
      <div className="pt-2 text-xs text-muted">
        Наличие в других магазинах сети можно уточнить по <Link href="/stores">телефонам магазинов</Link>
      </div>
    </>
  )
}
