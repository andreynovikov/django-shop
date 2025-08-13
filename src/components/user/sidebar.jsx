import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';

import Collapse from 'react-bootstrap/Collapse';

import UserAvatar from '@/components/user/avatar';
import UserBonus from '@/components/user/bonus';

import { formatPhone } from '@/lib/format';
import useFavorites from '@/lib/favorites';
import { useSession, signOut } from '@/lib/session';
import { orderKeys, loadOrders } from '@/lib/queries';

export default function UserSidebar() {
    const [menuOpen, setMenuOpen] = useState(false);

    const router = useRouter();
    const { user, status } = useSession({
        onUnauthenticated() {
            router.push({
                pathname: '/login',
                query: { callbackUrl: router.asPath }
            });
        }
    });

    const { favorites } = useFavorites();

    const { data: orders } = useQuery({
        queryKey: orderKeys.list(1, ''),
        queryFn: () => loadOrders(1, ''),
        enabled: status === 'authenticated'
    });

    if (status === 'loading' || !!!user) {
        return (
            <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
                <div className="bg-white rounded-3 shadow-lg pt-1 mb-5 mb-lg-0" style={{height: 320}}> { /* TODO: use placeholders */}
                </div>
            </aside>
        )
    }

    return (
        <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
            <div className="bg-white rounded-3 shadow-lg pt-1 mb-5 mb-lg-0">
                <div className="d-md-flex justify-content-between align-items-center text-center text-md-start p-4">
                    <div className="d-md-flex align-items-center">
                        <div className="img-thumbnail rounded-circle position-relative flex-shrink-0 mx-auto mb-2 mx-md-0 mb-md-0" style={{width: "6.375rem"}}>
                            <UserBonus />
                            <picture>
                                <UserAvatar gravatar={user.gravatar} name={ user.name || user.full_name } size="90" />
                            </picture>
                        </div>
                        <div className="ps-md-3">
                            <h3 className="fs-base mb-0">{ user.name || user.full_name }</h3>
                            <span className="text-accent fs-sm">{ formatPhone(user.phone) }</span>
                        </div>
                    </div>
                    <button className="btn btn-primary d-lg-none mb-2 mt-3 mt-md-0" onClick={() => setMenuOpen(!menuOpen)}>
                        <i className="ci-menu me-2" />Личный кабинет
                    </button>
                </div>
                <Collapse in={menuOpen} className="d-lg-block">
                    <ul className="list-unstyled mb-0">
                        <li className="border-bottom mb-0">
                            <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/orders' ? " active" : "")} href="/user/orders">
                                <i className="ci-bag opacity-60 me-2" />Заказы
                                { orders?.count > 0 && <span className="fs-sm text-muted ms-auto">{ orders.count }</span> }
                            </Link>
                        </li>
                        <li className="border-bottom mb-0">
                            <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/favorites' ? " active" : "")} href="/user/favorites">
                                <i className="ci-heart opacity-60 me-2" />Избранное
                                { favorites.length > 0 && <span className="fs-sm text-muted ms-auto">{ favorites.length }</span> }
                            </Link>
                        </li>
                        <li className="mb-0">
                            <Link className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/profile' ? " active" : "")} href="/user/profile">
                                <i className="ci-user opacity-60 me-2" />Профиль
                            </Link>
                        </li>
                        <li className="d-lg-none border-top mb-0">
                            <a className="nav-link-style d-flex align-items-center px-4 py-3" onClick={() => signOut({callbackUrl: '/'})} style={{cursor:'pointer'}}>
                                <i className="ci-sign-out opacity-60 me-2" />Выйти
                            </a>
                        </li>
                    </ul>
                </Collapse>
            </div>
        </aside>
    )
}
