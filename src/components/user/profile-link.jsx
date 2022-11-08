import { useRef } from 'react';
import Link from 'next/link';

import { useSession, signOut } from '@/lib/session';

import SignInModal from '@/components/sign-in-modal';

export default function UserProfileLink() {
    const modalRef = useRef();
    const { user, status } = useSession();

    if (status === 'authenticated') {
        return (
            <div className="navbar-tool ms-1 ms-lg-0 me-n1 me-lg-2 dropdown">
                <a className="navbar-tool-icon-box d-block dropdown-toggle" href="shop:user_orders">
                    <i className="navbar-tool-icon ci-user" />
                </a>
                <a className="navbar-tool-text ms-n3">
                    <small>{ user?.name || user?.phone }</small>личный кабинет
                </a>
                <div className="dropdown-menu dropdown-menu-end">
                    <Link href="/user/orders">
                        <a className="dropdown-item">Заказы</a>
                    </Link>
                    <Link href="/user/profile">
                        <a className="dropdown-item">Профиль</a>
                    </Link>
                    <div className="dropdown-divider"></div>
                    <a className="dropdown-item" onClick={signOut} style={{cursor:'pointer'}}>Выйти</a>
                </div>
            </div>
        )
    } else {
        return (
            <div className="navbar-tool ms-1 ms-lg-0 me-n1 me-lg-2">
                <SignInModal ref={modalRef} />
                <a className="navbar-tool-icon-box d-block" onClick={() => modalRef.current.showModal()} style={{cursor:'pointer'}}>
                    <i className="navbar-tool-icon ci-user" />
                </a>
                <a className="navbar-tool-text ms-n3" onClick={() => modalRef.current.showModal()} style={{cursor:'pointer'}}>
                    <small>Вход в</small>аккаунт
                </a>
            </div>
        )
    }
}
