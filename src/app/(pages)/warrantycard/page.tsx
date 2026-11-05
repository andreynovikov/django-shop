import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import WarrantyCardForm from '@/components/warranty/card-form'

const title = 'Печать гарантийного талона'

// The page is static, the card is loaded in the browser
export const metadata: Metadata = {
  title,
}

export default function WarrantyCardPage() {
  return pageContentWrapper({
    title,
    children: (
      <div className="mb-12 px-3">
        <div className="md:mx-auto md:w-1/2">
          <WarrantyCardForm />
        </div>
      </div>
    ),
  })
}
