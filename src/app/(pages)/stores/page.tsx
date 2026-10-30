import { Metadata } from 'next'
import { SearchParams } from 'nuqs/server'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import { loadStores } from '@/lib/queries'
import { storeSearchParamsCache } from '@/lib/search-params'

import { StoreList } from '@/components/store/list'

export const metadata: Metadata = {
  title: 'Адреса магазинов',
}

type PageProps = {
  searchParams: Promise<SearchParams>
}

export default async function StoresPage({ searchParams }: PageProps) {
  const resolvedParams = await searchParams
  const { marketplace, lottery } = storeSearchParamsCache.parse(resolvedParams)

  const title =
    marketplace ? "В этих магазинах можно пройти бесплатное обучение работе на швейной машине при предъявлении гарантийного талона" :
      lottery ? "Покупатели этих магазинов принимают участие в юбилейной лотерее" :
        "Наши магазины рядом с Вами"

  const stores = await loadStores({ marketplace, lottery })

  return pageContentWrapper({
    title,
    children: (
      <StoreList stores={stores} />
    )
  })
}
