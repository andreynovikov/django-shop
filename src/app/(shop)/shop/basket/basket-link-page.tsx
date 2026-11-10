import { ReactNode } from 'react'
import { Metadata } from 'next'

export const basketLinkMetadata: Metadata = {
  title: 'Корзина',
  robots: { index: false },
}

// The pages at the paths of the links in the backend's abandoned basket email
export function BasketLinkPage({ children }: { children: ReactNode }) {
  return (
    <div className="container my-6 py-4 lg:py-6">
      <div className="md:flex md:justify-center">
        <div className="md:w-1/2">
          {children}
        </div>
      </div>
    </div>
  )
}
