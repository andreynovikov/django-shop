import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'
import ExtendWarrantyForm from '@/components/warranty/extend-form'

const title = 'Расширение гарантии'

// The page is static, the session is loaded in the browser
export const metadata: Metadata = {
  title,
}

export default function ExtendWarrantyPage() {
  return pageContentWrapper({
    title,
    children: <ExtendWarrantyForm />,
  })
}
