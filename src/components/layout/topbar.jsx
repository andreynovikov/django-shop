import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

import CartNotice from '@/components/cart/notice';
import Catalog from '@/components/catalog';
import CompareLink from '@/components/user/compare-link';
import UserProfileLink from '@/components/user/profile-link';
import ProductSearchInput from '@/components/product/search-input';

import useComparison from '@/lib/comparison';
import useFavorites from '@/lib/favorites';
import { useSite } from '@/lib/site';
import { useSession } from '@/lib/session';
import { formatPhone } from '@/lib/format';

export default function TopBar({hideSignIn, hideCartNotice}) {
    const [catalogVisible, setCatalogVisible] = useState(false);
    const { site } = useSite();
    const { status } = useSession();
    const catalogButtonRef = useRef(null);

    useEffect(() => {
        const toggler = document.querySelector('.navbar-stuck-toggler');

        const handleToggle = (event) => {
            const stuckMenu = document.querySelector('.navbar-stuck-menu');
            stuckMenu.classList.toggle('show');
            event.preventDefault();
        };

        const setStickyState = (event) => {
            const topbar = document.querySelector('.topbar');
            const navbar = document.querySelector('.navbar-sticky');
            const navbarHeight = navbar.offsetHeight;
            if (event.currentTarget.pageYOffset > topbar.offsetHeight) {
                document.body.style.paddingTop = navbarHeight + 'px';
                navbar.classList.add('navbar-stuck');
            } else {
                document.body.style.paddingTop = '';
                navbar.classList.remove('navbar-stuck');
            }
        };

        toggler.addEventListener('click', handleToggle);
        window.addEventListener('scroll', setStickyState);

        return () => {
            toggler.removeEventListener('click', handleToggle);
            window.removeEventListener('scroll', setStickyState);
        };
    }, []);

    const { comparisons } = useComparison();
    const { favorites } = useFavorites();

    const seoLogoAlt = "Швейный Мир - всероссийская сеть швейных супермаркетов.&#10; Швейные машинки, вышивальные и вязальные машины, оверлоки и аксессуары.";

    return (
        <>
            <div className="topbar topbar-light sw-bg-light">
                <div className="container">
                    <div className="topbar-text dropdown d-md-none">
                        <a className="topbar-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Useful links</a>
                        <ul className="dropdown-menu">
                            { site.phone && (
                                <li>
                                    <a className="dropdown-item" href={"tel:" + site.phone}>
                                        <i className="ci-support text-muted me-2" />{ formatPhone(site.phone) }
                                    </a>
                                </li>
                            )}
                            { comparisons.length > 0 && (
                                <li>
                                    <Link className="dropdown-item" href="/compare/" rel="nofollow">
                                        <CompareLink mobile />
                                    </Link>
                                </li>
                            )}
                            <li>
                                <Link className="dropdown-item" href="/user/orders?track" rel="nofollow">
                                    <i className="ci-delivery text-muted me-2" />Отслеживание заказа
                                </Link>
                            </li>
                        </ul>
                    </div>
                    <div className="d-none d-md-inline-block">
                        { site.phone && (
                            <div className="topbar-text text-nowrap">
                                <i className="ci-support mt-n1" />
                                <a className="topbar-link" href={"tel:" + site.phone}>{ formatPhone(site.phone) }</a>
                                <span className="text-muted d-none d-lg-inline">&nbsp;&ndash;&nbsp;интернет-магазин</span>
                            </div>
                        )}
                        <div className="topbar-text text-nowrap border-start ps-3 ms-3">
                            <i className="ci-location mt-n1" />
                            <span className="text-muted me-1">
                                <Link className="topbar-link" href="/stores/">Адреса магазинов</Link>
                            </span>
                        </div>
                    </div>
                    <div className="d-none d-md-inline-block">
                        { comparisons.length > 0 && (
                            <Link className="topbar-link text-nowrap border-end pe-3 me-3" href="/compare" rel="nofollow">
                                <CompareLink />
                            </Link>
                        )}
                        <Link className="topbar-link text-nowrap" href="/user/orders?track" rel="nofollow">
                            <i className="ci-delivery mt-n1" />Отслеживание заказа
                        </Link>
                    </div>
                </div>
            </div>
            <div className="navbar-sticky bg-light">
                <div className="navbar navbar-expand-lg navbar-light">
                    <div className="container">
                        <Link className="navbar-brand flex-shrink-0" href="/">
                            <img src="/i/logo.svg" alt={seoLogoAlt} />
                        </Link>
                        { /*
                        <Link className="navbar-brand d-none d-sm-block d-xl-none flex-shrink-0" href="/">
                            <img src="/i/logo.svg" alt={seoLogoAlt} style={{ height: 34, width: 'auto' }} />
                        </Link>
                        <Link className="navbar-brand d-sm-none flex-shrink-0" href="/">
                            <img src="/i/logo-icon.svg" alt={seoLogoAlt} style={{ height: 34, width: 'auto' }} />
                        </Link>
                          */
                        }
                        <div className="d-none d-lg-flex w-100 mx-4">
                            <ProductSearchInput />
                        </div>
                        <div className="navbar-toolbar d-flex flex-shrink-0 align-items-center">
                            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse">
                                <span className="navbar-toggler-icon"></span>
                            </button>
                            <a className="navbar-tool navbar-stuck-toggler" href="#">
                                <span className="navbar-tool-tooltip">Раскрыть меню</span>
                                <div className="navbar-tool-icon-box"><i className="navbar-tool-icon ci-menu" /></div>
                            </a>
                            { status === 'authenticated' && (
                                <Link className="navbar-tool d-none d-lg-flex" href="/user/favorites">
                                    <div className="navbar-tool-icon-box">
                                        { favorites.length > 0 && <span className="navbar-tool-label">{ favorites.length }</span> }
                                        <i className="navbar-tool-icon ci-heart" />
                                    </div>
                                    <span className="navbar-tool-tooltip">Избранное</span>
                                </Link>
                            )}
                            { !hideSignIn && <UserProfileLink /> }
                            { !hideCartNotice && <CartNotice /> }

                        </div>
                    </div>
                </div>
                <div className="navbar navbar-expand-lg navbar-light navbar-stuck-menu mt-n2 pt-0 pb-2">
                    <div className="container">
                        <div className="collapse navbar-collapse" id="navbarCollapse">
                            <div className="d-lg-none my-3">
                                <ProductSearchInput mobile />
                            </div>
                            <ul className="navbar-nav navbar-mega-nav pe-lg-2 me-lg-2">
                                { /*
                                <li className="nav-item">
                                    <button ref={catalogButtonRef}
                                        className="btn btn-primary fw-bold w-100 text-start text-lg-center dropdown-toggle"
                                        onClick={() => setCatalogVisible(!catalogVisible)}>
                                        <i className={(catalogVisible ? "ci-close" : "ci-menu") + " align-middle mt-n1 me-2"} />Каталог
                                    </button>
                                </li>
                                  */
                                }
                                <li className="nav-item dropdown">
                                    <a className="nav-link dropdown-toggle ps-lg-0 fw-bold" href="#" data-bs-toggle="dropdown">
                                        <i className="ci-view-grid me-2" />Каталог
                                    </a>
                                    { /* className="btn btn-primary fw-bold w-100 text-start text-lg-center dropdown-toggle" */ }
                                    <div className="dropdown-menu px-2 pb-4">
                                        <Catalog visible={true} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} />
                                    </div>
                                </li>
                            </ul>
                            <ul className="navbar-nav">
                                { /* <li class="nav-item"><a class="nav-link" href="{% url 'sales_actions' %}">Акции</a></li> */ }
                                <li className="nav-item">
                                    <Link className="nav-link" href="/pages/articles/">
                                        Справочные материалы
                                    </Link>
                                </li>
                                <li className="nav-item"><a className="nav-link" href="% url 'zinnia:entry_archive_index' %">Блог</a></li>
                                { /*
                                    <li className="nav-item dropdown"><a className="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Форум</a>
                                    <ul class="dropdown-menu">
                                    {#<li><a class="dropdown-item" href="{% url "spirit:topic:unread:index" %}">Непрочитанные темы</a></li>#}
                                    {#<li><a class="dropdown-item" href="{% url 'spirit:topic:index-active' %}">Активные темы</a></li>#}
                                    <li><a class="dropdown-item" href="{% url 'forum:index' %}">Архив</a></li>
                                    </ul>
                                    </li>
                                  */
                                }
                                <li className="nav-item d-md-none">
                                    <Link className="nav-link" href="/stores/">
                                        Магазины
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" href="/service/">
                                        Сервисные центры
                                    </Link>
                                </li>
                                <li className="nav-item">
                                    <Link className="nav-link" href="/pages/delivery/">
                                        Доставка и оплата
                                    </Link>
                                </li>
                            </ul>

                        </div>
                    </div>
                </div>
            </div>
        { /* <Catalog visible={catalogVisible} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} /> */ }
        </>
    )
}
