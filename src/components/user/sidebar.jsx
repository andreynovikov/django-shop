import { useRouter } from 'next/router';
import Link from 'next/link';
import { useQuery } from 'react-query';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars, faRightFromBracket } from '@fortawesome/free-solid-svg-icons';
import { faWindowRestore, faUser } from '@fortawesome/free-regular-svg-icons';

import UserAvatar from '@/components/user/avatar';

import { formatPhone } from '@/lib/format';
import { useSite } from '@/lib/site';
import { useSession, signOut } from '@/lib/session';
import { orderKeys, loadOrders } from '@/lib/queries';

export default function UserSidebar() {
    const router = useRouter();
    const { site } = useSite();
    const { user, status } = useSession({
        onUnauthenticated() {
            router.push({
                pathname: '/login',
                query: { callbackUrl: router.asPath }
            });
        }
    });

    const { data: orders } = useQuery(
        orderKeys.list(1, ''),
        () => loadOrders(1, '', site.id),
        {
            enabled: status === 'authenticated' && site.id > 0
        }
    );

    if (status === 'loading' || !!!user) {
        return (
            <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
                <div className="bg-white rounded-3 shadow-sm pt-1 mb-5 mb-lg-0" style={{height: 320}}> { /* TODO: use placeholders */}
                </div>
            </aside>
        )
    }

    return (
        <aside className="col-lg-4 pt-4 pt-lg-0 pe-xl-5">
            <div className="bg-white rounded-3 shadow-sm pt-1 mb-5 mb-lg-0">
                <div className="d-md-flex justify-content-between align-items-center text-center text-md-start p-4">
                    <div className="d-md-flex align-items-center">
                        <div className="img-thumbnail rounded-circle position-relative flex-shrink-0 mx-auto mb-2 mx-md-0 mb-md-0">
                            { user.discount > 0 && (
                                <span className="badge bg-warning position-absolute top-0 end-0 translate-middle-y" data-bs-toggle="tooltip" title="Текущая скидка">
                                    { /* TODO: показывать бонусы */ }
                                    { user.discount }%
                                </span>
                            )}
                            <picture>
                                <UserAvatar gravatar={user.gravatar} name={ user.name || user.full_name } size="60" />
                            </picture>
                        </div>
                        <div className="ps-md-3">
                            <h3 className="fs-base mb-0">{ user.name || user.full_name }</h3>
                            <span className="text-accent fs-sm">{ formatPhone(user.phone) }</span>
                        </div>
                    </div>
                    <a className="btn btn-primary d-lg-none mb-2 mt-3 mt-md-0" href="#account-menu" data-bs-toggle="collapse" aria-expanded="false">
                        <FontAwesomeIcon icon={faBars} className="me-1" />
                        Личный кабинет
                    </a>
                </div>
                <div className="d-lg-block collapse" id="account-menu">
                    <ul className="list-unstyled mb-0">
                        <li className="border-bottom mb-0">
                            <Link className={"nav-link-style d-flex align-items-baseline px-4 py-3" + (router.pathname === '/user/orders' ? " active" : "")} href="/user/orders">
                                <FontAwesomeIcon icon={faWindowRestore} className="me-1" />
                                Заказы
                                { orders?.count > 0 && <span className="fs-sm text-muted ms-auto">{ orders.count }</span> }
                            </Link>
                        </li>
                        <li className="border-bottom mb-0">
                            <Link className={"nav-link-style d-flex px-4 py-3" + (router.pathname === '/user/profile' ? " active" : "")} href="/user/profile">
                                <FontAwesomeIcon icon={faUser} className="me-1" />
                                Профиль
                            </Link>
                        </li>
                        <li className="mb-0">
                            <a className="nav-link-style d-flex px-4 py-3" onClick={() => signOut({callbackUrl: '/'})} style={{cursor:'pointer'}}>
                                <FontAwesomeIcon icon={faRightFromBracket} className="me-1" />
                                Выйти
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </aside>
    )
}
