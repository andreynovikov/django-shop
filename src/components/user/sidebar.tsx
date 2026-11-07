'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'

import { Collapsible } from '@base-ui/react/collapsible'
import { IconHeart, IconLogout2, IconMenu2, IconShoppingBag, IconUser } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'
import { navLinkClass } from '@/components/ui/nav'

import UserAvatar from '@/components/user/avatar'
// import UserBonus from '@/components/user/bonus'

import { formatPhone } from '@/lib/format'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { orderKeys, loadOrders } from '@/lib/queries'
import { User } from '@/lib/types'

const menuLinkClass = 'flex items-center px-6 py-4'
const menuIcon = { size: 18, stroke: 1.5, className: 'me-2 opacity-60' }

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

  const { favorites } = useFavorites()

  const { data: orders } = useQuery({
    queryKey: orderKeys.list(1, ''),
    queryFn: () => loadOrders(1, ''),
    enabled: status === 'authenticated'
  })

  if (status === 'loading' || !!!user) {
    return (
      <aside className="pt-6 lg:pt-0 xl:pe-8">
        <div className="mb-12 h-80 rounded-lg bg-white pt-1 shadow-lg lg:mb-0"> { /* TODO: use placeholders */}
        </div>
      </aside>
    )
  }

  return (
    <aside className="pt-6 lg:pt-0 xl:pe-8">
      <Collapsible.Root className="mb-12 rounded-lg bg-white pt-1 shadow-lg lg:mb-0" open={menuOpen} onOpenChange={open => setMenuOpenAt(open ? pathname : null)}>
        <div className="p-6 text-center md:flex md:items-center md:justify-between md:text-start">
          <div className="md:flex md:items-center">
            <div className="relative mx-auto mb-2 w-[6.375rem] shrink-0 rounded-full border bg-white p-1 md:mx-0 md:mb-0">
              {/* <UserBonus /> */}
              <picture>
                <UserAvatar gravatar={user.gravatar} name={user.name || user.full_name} size={90} />
              </picture>
            </div>
            <div className="md:ps-4">
              <h3 className="mb-0 text-base leading-[1.2] font-medium">{user.name || user.full_name}</h3>
              <span className="text-sm text-accent">{formatPhone(user.phone)}</span>
            </div>
          </div>
          <Collapsible.Trigger className={`${buttonClass()} mt-4 mb-2 md:mt-0 lg:hidden`}>
            <IconMenu2 size={18} stroke={1.5} className="me-2" />Личный кабинет
          </Collapsible.Trigger>
        </div>
        {/* shown from lg up, a collapsing menu below lg */}
        <Collapsible.Panel
          className="sw-shown-lg max-lg:h-(--collapsible-panel-height) max-lg:overflow-hidden max-lg:transition-[height] max-lg:duration-350 max-lg:data-ending-style:h-0 max-lg:data-starting-style:h-0"
          keepMounted>
          <ul>
            <li className="border-b">
              <Link className={`${navLinkClass({ active: pathname === '/user/orders/' })} ${menuLinkClass}`} href="/user/orders/" aria-current={pathname === '/user/orders/' ? 'page' : undefined}>
                <IconShoppingBag {...menuIcon} />Заказы
                {orders !== undefined && orders.count > 0 && <span className="ms-auto text-sm text-muted">{orders.count}</span>}
              </Link>
            </li>
            <li className="border-b">
              <Link className={`${navLinkClass({ active: pathname === '/user/favorites/' })} ${menuLinkClass}`} href="/user/favorites/" aria-current={pathname === '/user/favorites/' ? 'page' : undefined}>
                <IconHeart {...menuIcon} />Избранное
                {favorites.length > 0 && <span className="ms-auto text-sm text-muted">{favorites.length}</span>}
              </Link>
            </li>
            <li>
              <Link className={`${navLinkClass({ active: pathname === '/user/profile/' })} ${menuLinkClass}`} href="/user/profile/" aria-current={pathname === '/user/profile/' ? 'page' : undefined}>
                <IconUser {...menuIcon} />Профиль
              </Link>
            </li>
            <li className="border-t">
              <button type="button" className={`${navLinkClass()} ${menuLinkClass} w-full`} onClick={handleSignOut}>
                <IconLogout2 {...menuIcon} />Выйти
              </button>
            </li>
          </ul>
        </Collapsible.Panel>
      </Collapsible.Root>
    </aside>
  )
}
