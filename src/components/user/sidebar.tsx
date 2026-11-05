'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'

import { Collapsible } from '@base-ui/react/collapsible'

import { IconLogout, IconMenu2, IconShoppingBag, IconUser } from '@tabler/icons-react'

import UserAvatar from '@/components/user/avatar'
import { buttonClass } from '@/components/ui/button'
// import UserBonus from '@/components/user/bonus'

import { formatPhone } from '@/lib/format'
import { useSession } from '@/lib/session'
import { useSite } from '@/lib/site'
import { orderKeys, loadOrders } from '@/lib/queries'
import { User } from '@/lib/types'

export default function UserSidebar() {
  const [signingOut, setSigningOut] = useState(false)

  const router = useRouter()
  const pathname = usePathname()

  // The sidebar stays mounted in the account layout, the menu is open on the page it was opened on only
  const [menuOpenAt, setMenuOpenAt] = useState<string | null>(null)
  const menuOpen = menuOpenAt === pathname

  // Signing out navigates to the home page, which is still loading when the session ends,
  // so the login page must not take over meanwhile.
  const { user: sessionUser, status, signOut } = useSession({
    onUnauthenticated: signingOut ? undefined : () => router.push(`/login?callbackUrl=${encodeURIComponent(window.location.pathname + window.location.search)}`)
  })

  const handleSignOut = () => {
    setSigningOut(true)
    signOut({ callbackUrl: '/' })
  }
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const { site } = useSite()

  // counts the orders made on this site only, the site is the same for every query of the storefront
  // eslint-disable-next-line @tanstack/query/exhaustive-deps
  const { data: orders } = useQuery({
    queryKey: orderKeys.list(1, ''),
    queryFn: () => loadOrders(1, '', site.id),
    enabled: status === 'authenticated' && site.id !== undefined
  })

  if (status === 'loading' || !!!user) {
    return (
      <aside className="pt-6 lg:pt-0 xl:pe-12">
        <div className="mb-12 rounded-lg bg-white pt-1 shadow-lg lg:mb-0" style={{ height: 320 }}> { /* TODO: use placeholders */}
        </div>
      </aside>
    )
  }

  return (
    <aside className="pt-6 lg:pt-0 xl:pe-12">
      <Collapsible.Root className="mb-12 rounded-lg bg-white pt-1 shadow-lg lg:mb-0" open={menuOpen} onOpenChange={open => setMenuOpenAt(open ? pathname : null)}>
        <div className="items-center justify-between p-6 text-center md:flex md:text-start">
          <div className="items-center md:flex">
            <div className="relative mx-auto mb-2 shrink-0 rounded-full border bg-white p-1 md:mx-0 md:mb-0" style={{ width: "6.375rem" }}>
              {/* <UserBonus /> */}
              <picture>
                <UserAvatar gravatar={user.gravatar} name={user.name || user.full_name} size={90} />
              </picture>
            </div>
            <div className="md:ps-4">
              <h3 className="leading-none font-light">{user.name || user.full_name}</h3>
              <span className="text-xs text-accent">{formatPhone(user.phone)}</span>
            </div>
          </div>
          <Collapsible.Trigger className={`${buttonClass()} mt-4 mb-2 md:mt-0 lg:hidden`}>
            <IconMenu2 size={20} stroke={1.5} className="me-1" />Личный кабинет
          </Collapsible.Trigger>
        </div>
        {/* below lg the panel height is animated, from lg up it is always shown, see .sw-shown-lg in styles.css */}
        <Collapsible.Panel
          className="sw-shown-lg max-lg:h-(--collapsible-panel-height) max-lg:overflow-hidden max-lg:transition-[height] max-lg:duration-350 max-lg:data-ending-style:h-0 max-lg:data-starting-style:h-0"
          keepMounted>
          <ul>
            <li className="border-b">
              <Link className={"flex items-center px-6 py-4 hover:no-underline" + (pathname === '/user/orders/' ? " active" : "")} href="/user/orders/">
                <IconShoppingBag size={20} stroke={1.5} className="me-2 opacity-50" />Заказы
                {orders !== undefined && orders.count > 0 && <span className="ms-auto text-xs text-muted">{orders.count}</span>}
              </Link>
            </li>
            <li>
              <Link className={"flex items-center px-6 py-4 hover:no-underline" + (pathname === '/user/profile/' ? " active" : "")} href="/user/profile/">
                <IconUser size={20} stroke={1.5} className="me-2 opacity-50" />Профиль
              </Link>
            </li>
            <li className="border-t">
              <a className="flex items-center px-6 py-4 hover:no-underline" onClick={handleSignOut} style={{ cursor: 'pointer' }}>
                <IconLogout size={20} stroke={1.5} className="me-2 opacity-50" />Выйти
              </a>
            </li>
          </ul>
        </Collapsible.Panel>
      </Collapsible.Root>
    </aside>
  )
}
