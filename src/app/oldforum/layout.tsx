import { ReactNode } from 'react'
import { Metadata } from 'next'

import { pageContentWrapper } from '@/components/layout/page-content-wrapper'

const title = 'Архив форума'

export const metadata: Metadata = {
  title,
}

export default function OldForumLayout({ children }: { children: ReactNode }) {
  return pageContentWrapper({ title, children })
}
