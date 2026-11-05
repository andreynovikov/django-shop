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
      <div className="container mb-5">
        <div className="row justify-content-md-center">
          <div className="col-md-6">
            <WarrantyCardForm />
          </div>
        </div>
      </div>
    ),
  })
}
