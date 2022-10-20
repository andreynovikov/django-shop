import { forwardRef, useImperativeHandle, useRef } from 'react';
import Link from 'next/link';
import { signOut, useSession } from 'next-auth/react';

import SignInModal from '@/components/sign-in-modal';

export default function UserProfileLink() {
    const modalRef = useRef();
    const { data: session, status } = useSession();

    if (status === 'authenticated') {
        console.log(session);
        return (
            <div className="navbar-tool ms-1 ms-lg-0 me-n1 me-lg-2 dropdown">
                <a className="navbar-tool-icon-box d-block dropdown-toggle" href="shop:user_orders">
                    <i className="navbar-tool-icon ci-user" />
                </a>
                <a className="navbar-tool-text ms-n3">
                    <small>{ session.user?.name || session.user?.phone }</small>личный кабинет
                </a>
                <div className="dropdown-menu dropdown-menu-end">
                    <a className="dropdown-item" href="">Заказы</a>
                    <a className="dropdown-item" href="">Профиль</a>
                    <div className="dropdown-divider"></div>
                    <a className="dropdown-item" onClick={() => signOut()} style={{cursor:'pointer'}}>Выйти</a>
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
