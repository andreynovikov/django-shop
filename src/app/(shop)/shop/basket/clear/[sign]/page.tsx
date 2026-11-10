import BasketLink from '@/components/cart/basket-link'

import { BasketLinkPage, basketLinkMetadata } from '../../basket-link-page'

export const metadata = basketLinkMetadata

// The basket id signed by the backend
export default async function ClearBasketPage({ params }: PageProps<'/shop/basket/clear/[sign]'>) {
  const { sign } = await params // still encoded: Next escapes ',' and ':' in segments
  return (
    <BasketLinkPage>
      <BasketLink action="clear" value={decodeURIComponent(sign)} />
    </BasketLinkPage>
  )
}
