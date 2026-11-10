import BasketLink from '@/components/cart/basket-link'

import { BasketLinkPage, basketLinkMetadata } from '../../basket-link-page'

export const metadata = basketLinkMetadata

// '<product id>*<quantity>,...', the backend parses it
export default async function RestoreBasketPage({ params }: PageProps<'/shop/basket/restore/[contents]'>) {
  const { contents } = await params // still encoded: Next escapes ',' and ':' in segments
  return (
    <BasketLinkPage>
      <BasketLink action="restore" value={decodeURIComponent(contents)} />
    </BasketLinkPage>
  )
}
