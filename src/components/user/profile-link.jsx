import { useRef } from 'react';
import Link from 'next/link';

import { formatPhone } from '@/lib/format';
import { useSession, signOut } from '@/lib/session';

import SignInModal from '@/components/user/sign-in-modal';

export default function UserProfileLink() {
    const modalRef = useRef();
    const { user, status } = useSession();

    if (status === 'authenticated') {
        return (
            <div className="navbar-tool ms-1 ms-lg-0 me-n1 me-lg-2 dropdown">
                <Link className="navbar-tool-icon-box d-block dropdown-toggle" href="/user/orders">
                    <i className="navbar-tool-icon ci-user" />
                </Link>
                <a className="navbar-tool-text ms-n3" style={{cursor:'pointer'}}>
                    <small>{ user?.name || formatPhone(user?.phone) }</small>личный кабинет
                </a>
                <div className="dropdown-menu dropdown-menu-end">
                    <Link className="dropdown-item" href="/user/orders">
                        Заказы
                    </Link>
                    <Link className="dropdown-item" href="/user/profile">
                        Профиль
                    </Link>
                    <div className="dropdown-divider"></div>
                    <a className="dropdown-item" onClick={signOut} style={{cursor:'pointer'}}>Выйти</a>
                </div>
            </div>
        )
    } else {
        return (
            <div className="navbar-tool ms-1 ms-lg-0 me-n1 me-lg-2">
                <SignInModal ref={modalRef} ctx="profile" />
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
