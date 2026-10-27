import { useState } from 'react'
import Link from 'next/link'
import { useQuery } from '@tanstack/react-query'

import { Collapsible } from '@base-ui/react/collapsible'

import UserAvatar from '@/components/user/avatar'
// import UserBonus from '@/components/user/bonus'

import { formatPhone } from '@/lib/format'
import useFavorites from '@/lib/favorites'
import { useSession } from '@/lib/session'
import { useNavigation } from '@/lib/navigation'
import { orderKeys, loadOrders } from '@/lib/queries'
import { User } from '@/lib/types'

export default function UserSidebar() {
  const [menuOpen, setMenuOpen] = useState(false)

  const { navigate, path } = useNavigation()

  const { user: sessionUser, status, signOut } = useSession({
    onUnauthenticated: () => navigate(`/login?callbackUrl=${encodeURIComponent(path)}`)
  })
  const user = status === 'authenticated' ? sessionUser as User : undefined

  const { favorites } = useFavorites()

  const { data: orders } = useQuery({
    queryKey: orderKeys.list(1, ''),
    queryFn: () => loadOrders(1, ''),
    enabled: status === 'authenticated'
  })

  if (status === 'loading' || !!!user) {
    return (
      <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
        <div className="bg-white rounded-3 shadow-lg pt-1 mb-5 mb-lg-0" style={{ height: 320 }}> { /* TODO: use placeholders */}
        </div>
      </aside>
    )
  }

  return (
    <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
      <Collapsible.Root className="bg-white rounded-3 shadow-lg pt-1 mb-5 mb-lg-0" open={menuOpen} onOpenChange={setMenuOpen}>
        <div className="d-md-flex justify-content-between align-items-center text-center text-md-start p-4">
          <div className="d-md-flex align-items-center">
            <div className="img-thumbnail rounded-circle position-relative flex-shrink-0 mx-auto mb-2 mx-md-0 mb-md-0" style={{ width: "6.375rem" }}>
              {/* <UserBonus /> */}
              <picture>
                <UserAvatar gravatar={user.gravatar} name={user.name || user.full_name} size={90} />
              </picture>
            </div>
            <div className="ps-md-3">
              <h3 className="fs-base mb-0">{user.name || user.full_name}</h3>
              <span className="text-accent fs-sm">{formatPhone(user.phone)}</span>
            </div>
          </div>
          <Collapsible.Trigger className="btn btn-primary d-lg-none mb-2 mt-3 mt-md-0">
            <i className="ci-menu me-2" />Личный кабинет
          </Collapsible.Trigger>
        </div>
        <Collapsible.Panel className="sw-collapse-lg-down d-lg-block" keepMounted>
          <ul className="list-unstyled mb-0">
            <li className="border-bottom mb-0">
              <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (path === '/user/orders/' ? " active" : "")} href="/user/orders/">
                <i className="ci-bag opacity-60 me-2" />Заказы
                {orders !== undefined && orders.count > 0 && <span className="fs-sm text-muted ms-auto">{orders.count}</span>}
              </Link>
            </li>
            <li className="border-bottom mb-0">
              <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (path === '/user/favorites/' ? " active" : "")} href="/user/favorites/">
                <i className="ci-heart opacity-60 me-2" />Избранное
                {favorites.length > 0 && <span className="fs-sm text-muted ms-auto">{favorites.length}</span>}
              </Link>
            </li>
            <li className="mb-0">
              <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (path === '/user/profile/' ? " active" : "")} href="/user/profile/">
                <i className="ci-user opacity-60 me-2" />Профиль
              </Link>
            </li>
            <li className="border-top mb-0">
              <a className="nav-link-style d-flex align-items-center px-4 py-3" onClick={() => signOut({ callbackUrl: '/' })} style={{ cursor: 'pointer' }}>
                <i className="ci-sign-out opacity-60 me-2" />Выйти
              </a>
            </li>
          </ul>
        </Collapsible.Panel>
      </Collapsible.Root>
    </aside>
  )
}
