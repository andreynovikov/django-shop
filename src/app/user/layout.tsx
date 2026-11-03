import { Metadata } from 'next'

// The account pages are static, the user's data is loaded in the browser
export const metadata: Metadata = {
  robots: { index: false },
}

export default function UserLayout({ children }: LayoutProps<'/user'>) {
  return children
}
