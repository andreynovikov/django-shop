import { ReactNode } from 'react'
import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

const title = 'Сравнение товаров'

export const metadata: Metadata = {
  title,
  robots: { index: false },
}

// The header is outside the loading boundary, so the static page has it
export default function CompareLayout({ children }: { children: ReactNode }) {
  return pageContentWrapper({
    title,
    dark: true,
    children: (
      <div className="container py-5 mb-2">
        {children}
      </div>
    ),
  })
}
