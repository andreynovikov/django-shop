import { useState } from 'react'
import Link from 'next/link'
import { IconUser } from '@tabler/icons-react'

import { hoverMenuClass, menuDividerClass, menuItemClass } from '@/components/ui/menu'
import { navbarToolCaptionClass, navbarToolClass, navbarToolIconClass, navbarToolTextClass } from '@/components/ui/navbar'

import { formatPhone } from '@/lib/format'
import { useSession } from '@/lib/session'

import SignInModal from '@/components/user/sign-in-modal'
import { User } from '@/lib/types'

export default function UserProfileLink() {
  const [showSignIn, setShowSignIn] = useState(false)
  const { user: sessionUser, status, signOut } = useSession()
  const user = status === 'authenticated' ? sessionUser as User : undefined

  if (status === 'authenticated') {
    return (
      <div className={`${navbarToolClass} -me-1 ms-1 flex lg:ms-0 lg:me-2`}>
        <Link className={navbarToolIconClass()} href="/user/orders" aria-label="Личный кабинет">
          <IconUser size={22} stroke={1.5} />
        </Link>
        <a className={`${navbarToolTextClass({ dropdown: true })} -ms-4`}>
          <small className={navbarToolCaptionClass}>{user?.name || formatPhone(user!.phone)}</small>личный кабинет
        </a>
        <div className={hoverMenuClass}>
          <Link className={menuItemClass} href="/user/orders">
            Заказы
          </Link>
          <Link className={menuItemClass} href="/user/profile">
            Профиль
          </Link>
          <div className={menuDividerClass}></div>
          <button type="button" className={menuItemClass} onClick={() => signOut()}>Выйти</button>
        </div>
      </div>
    )
  } else {
    return (
      <>
        <SignInModal ctx="profile" show={showSignIn} onHide={() => setShowSignIn(false)} />
        <button type="button" className={`${navbarToolClass} -me-1 ms-1 flex text-start lg:ms-0 lg:me-2`} onClick={() => setShowSignIn(true)} aria-label="Вход в личный кабинет">
          <span className={navbarToolIconClass()}>
            <IconUser size={22} stroke={1.5} />
          </span>
          <span className={`${navbarToolTextClass()} -ms-4`}>
            <small className={navbarToolCaptionClass}>Вход в</small>личный кабинет
          </span>
        </button>
      </>
    )
  }
}
