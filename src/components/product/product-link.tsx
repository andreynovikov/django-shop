import { ReactNode } from 'react'
import Link from 'next/link'

import { storefront } from '@/storefront'

// A link to the product's page, or only its content on a storefront without product pages
export default function ProductLink({ code, className, children }: { code: string, className?: string, children: ReactNode }) {
  if (!storefront.productPages)
    return <span className={className}>{children}</span>
  return <Link className={className} href={`/products/${code}`}>{children}</Link>
}
