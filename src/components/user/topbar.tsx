import { ReactNode } from 'react'

export default function TopSidebar({ children }: { children: ReactNode}) {
  return (
    <div className="items-center justify-between pb-4 lg:flex">
      {children}
    </div>
  )
}
