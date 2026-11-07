import { Fragment } from 'react'
import { Metadata } from 'next'
import Image from 'next/image'
import Link from 'next/link'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

import { loadSalesActions } from '@/lib/queries'

export const revalidate = 3600

export const metadata: Metadata = {
  title: 'Все акции',
}

export default async function SalesActionsPage() {
  const actions = await loadSalesActions()

  return pageContentWrapper({
    title: <>Акции сети магазинов &laquo;Швейный Мир&raquo;</>,
    children: (
      <div className="container mb-2 py-12 md:mb-6">
        {actions.map(action => (
          <Fragment key={action.id}>
            <h3 className="mb-3 text-h3">{action.name}</h3>
            <Link className="mb-12 block" href={`/actions/${action.slug}/`}>
              {action.image !== undefined ? (
                <Image
                  className="block h-auto max-w-full"
                  src={action.image}
                  width={action.image_width}
                  height={action.image_height}
                  alt={action.name} />
              ) : (
                <span>{action.name}</span>
              )}
            </Link>
          </Fragment>
        ))}
      </div>
    )
  })
}
