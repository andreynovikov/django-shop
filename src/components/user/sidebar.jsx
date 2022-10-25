import { useRouter } from 'next/router';
import Link from 'next/link';
import { signOut, useSession } from 'next-auth/react';
import { useQuery } from 'react-query';

import { formatPhone } from '@/lib/format';
import useFavorites from '@/lib/favorites';
import { withSession, orderKeys, userKeys, loadOrders, loadUser } from '@/lib/queries';

export default function UserSidebar() {
    const router = useRouter();
    const { data: session, status } = useSession({
        required: true,
        onUnauthenticated() {
            router.push({
                pathname: '/login',
                query: { callbackUrl: router.asPath }
            });
        },
    });

    const { data: user } = useQuery(
        userKeys.detail(session?.user),
        () => withSession(session, loadUser, session?.user),
        {
            enabled: status === 'authenticated'
        }
    );

    const { favorites } = useFavorites();

    const { data: orders } = useQuery(
        orderKeys.list(1, ''),
        () => withSession(session, loadOrders, 1, ''),
        {
            enabled: status === 'authenticated'
        }
    );

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
                            { user.discount > 0 && (
                                <span className="badge bg-warning position-absolute end-0 mt-n2" data-bs-toggle="tooltip" title="Текущая скидка">
                                    { /* TODO: показывать бонусы */ }
                                    { user.discount }%
                                </span>
                            )}
                            <img className="rounded-circle" src={user.gravatar} alt={ user.full_name } height="90" />
                        </div>
                        <div className="ps-md-3">
                            <h3 className="fs-base mb-0">{ user.name || user.full_name }</h3>
                            <span className="text-accent fs-sm">{ formatPhone(user.phone) }</span>
                        </div>
                    </div>
                    <a className="btn btn-primary d-lg-none mb-2 mt-3 mt-md-0" href="#account-menu" data-bs-toggle="collapse" aria-expanded="false">
                        <i className="ci-menu me-2" />Личный кабинет
                    </a>
                </div>
                <div className="d-lg-block collapse" id="account-menu">
                    <ul className="list-unstyled mb-0">
                        <li className="border-bottom mb-0">
                            <Link href="/user/orders">
                                <a className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/orders' ? " active" : "")}>
                                    <i className="ci-bag opacity-60 me-2" />Заказы
                                    { orders && <span className="fs-sm text-muted ms-auto">{ orders.count }</span> }
                                </a>
                            </Link>
                        </li>
                        <li className="border-bottom mb-0">
                            <Link href="/user/favorites">
                                <a className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/favorites' ? " active" : "")}>
                                    <i className="ci-heart opacity-60 me-2" />Избранное
                                    { favorites.length > 0 && <span className="fs-sm text-muted ms-auto">{ favorites.length }</span> }
                                </a>
                            </Link>
                        </li>
                        <li className="mb-0">
                            <Link href="/user/profile">
                                <a className={"nav-link-style d-flex align-items-center px-4 py-3" + (router.pathname === '/user/profile' ? " active" : "")}>
                                    <i className="ci-user opacity-60 me-2" />Профиль
                                </a>
                            </Link>
                        </li>
                        <li className="d-lg-none border-top mb-0">
                            <a className="nav-link-style d-flex align-items-center px-4 py-3" onClick={() => signOut({callbackUrl: '/'})} style={{cursor:'pointer'}}>
                                <i className="ci-sign-out opacity-60 me-2" />Выйти
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </aside>
    )
}
