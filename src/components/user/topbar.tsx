import { ReactNode } from 'react'

export default function TopSidebar({ children }: { children: ReactNode}) {
  return (
    <div className="pb-6 lg:mb-4 lg:flex lg:items-center lg:justify-between lg:pt-4 lg:pb-overlap">
      {children}
    </div>
  )
}
