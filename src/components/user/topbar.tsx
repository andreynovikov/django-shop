import { ReactNode } from 'react'

export default function TopSidebar({ children }: { children: ReactNode}) {
  return (
    <div className="d-lg-flex justify-content-between align-items-center pb-3">
      {children}
    </div>
  )
}
