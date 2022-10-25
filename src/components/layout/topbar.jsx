import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useSession } from 'next-auth/react';

import CartNotice from '@/components/cart/notice';
import Catalog from '@/components/catalog';
import UserProfileLink from '@/components/user/profile-link';
import ProductSearchInput from '@/components/product/search-input';

import useFavorites from '@/lib/favorites';

export default function Topbar({hideSignIn, hideCartNotice}) {
    const [catalogVisible, setCatalogVisible] = useState(false);
    const [searchText, setSearchText] = useState('');
    const { status } = useSession();
    const catalogButtonRef = useRef(null);

    const router = useRouter();

    useEffect(() => {
        if (router.query.text !== undefined)
            setSearchText(router.query.text);
    }, [router.query.text]);

    const { favorites } = useFavorites();

    const hide_search_form = false;

    const seoLogoAlt = "Швейный Мир - всероссийская сеть швейных супермаркетов.&#10; Швейные машинки, вышивальные и вязальные машины, оверлоки и аксессуары.";

    return (
        <>
            <div className="topbar topbar-light sw-bg-light">
                <div className="container">
                    <div>
                        <div className="topbar-text text-nowrap d-none d-md-inline-block">
                            <i className="ci-support mt-n1" />
                            <a className="topbar-link" href="tel:shop_info.inet_phone_E164">shop_info.inet_phone</a>
                            <span className="text-muted d-none d-lg-inline">&nbsp;&mdash;&nbsp;интернет-магазин</span>
                        </div>
                        <div className="topbar-text text-nowrap d-none d-md-inline-block border-start ps-3 ms-3">
                            <i className="ci-location mt-n1" />
                            <span className="text-muted me-1">
                                <a className="topbar-link" href="'stores'">Адреса магазинов</a>
                            </span>
                        </div>
                    </div>
                    <div className="topbar-text dropdown d-md-none ml-auto">
                        <a className="topbar-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
                            { status === 'authenticated' && <>Избранное / </> }
                            Сравнение / Отслеживание
                        </a>
                        <ul className="dropdown-menu dropdown-menu-end">
                            <li>
                                <a className="dropdown-item" href="tel:shop_info.inet_phone_E164" rel="nofollow">
                                    <i className="ci-support text-muted me-2" />shop_info.inet_phone
                                </a>
                            </li>
                            { /*
              {% if request.user.is_authenticated %}
              <li><a class="dropdown-item" href="{% url 'shop:favorites' %}" rel="nofollow"><i class="ci-heart text-muted me-2"></i>Избранное (<span id="dropdown-favorites-count"></span>)</a></li>
              {% endif %}
                              */
                            }
                            <li>
                                <a className="dropdown-item" href="'compare'" rel="nofollow">
                                    <i className="ci-compare text-muted me-2" />Сравнение (<span id="dropdown-compare-count"></span>)
                                </a>
                            </li>
                            <li>
                                <a className="dropdown-item" href="'shop:user_orders'" rel="nofollow">
                                    <i className="ci-delivery text-muted me-2" />Отслеживание заказа
                                </a>
                            </li>
                        </ul>
                    </div>
                    <div className="d-none d-md-block ml-3 text-nowrap">
                        { status === 'authenticated' && (
                            <a className="topbar-link d-none d-md-inline-block" href="'shop:favorites'" rel="nofollow">
                                <i className="ci-heart mt-n1" />Избранное <span id="favorites-notice">{ /* view "shop.views.favorites_notice" */ }</span>
                            </a>
                        )}
                        <a className="topbar-link ms-3 ps-3 border-start border-light d-none d-md-inline-block" href="'compare'" rel="nofollow">
                            <i className="ci-compare mt-n1" />Сравнение <span id="compare-notice">{ /* view "sewingworld.views.compare_notice" */ }</span>
                        </a>
                        <a className="topbar-link ms-3 ps-3 border-start d-none d-md-inline-block" href="'shop:user_orders'" rel="nofollow">
                            <i className="ci-delivery mt-n1"></i>Отслеживание заказа
                        </a>
                    </div>
                </div>
            </div>
            <div className="navbar-sticky bg-light">
                <div className="navbar navbar-expand-lg navbar-light">
                    <div className="container">
                        <Link href="/">
                            <a className="navbar-brand d-none d-lg-block me-3 flex-shrink-0">
                                <img src="/i/logo.svg" alt={seoLogoAlt} />
                            </a>
                        </Link>
                        <Link href="/">
                            <a className="navbar-brand d-lg-none me-2">
                                <img src="/i/logo-icon.svg" alt={seoLogoAlt} width="34" />
                            </a>
                        </Link>
                        { !hide_search_form && <ProductSearchInput /> }
                        <div className="navbar-toolbar d-flex flex-shrink-0 align-items-center">
                            <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse">
                                <span className="navbar-toggler-icon" />
                            </button>
                            <a className="navbar-tool navbar-stuck-toggler ms-1 me-2" href="#">
                                <div className="navbar-tool-icon-box"><i className="navbar-tool-icon ci-menu" /></div>
                                <div className="navbar-tool-text ms-n3">Меню</div>
                            </a>
                            { status === 'authenticated' && (
                                <Link href="/user/favorites">
                                    <a className="navbar-tool d-none d-lg-flex">
                                        <div className="navbar-tool-icon-box">
                                            { favorites.length > 0 && <span className="navbar-tool-label">{ favorites.length }</span> }
                                            <i className="navbar-tool-icon ci-heart" />
                                        </div>
                                        <span className="navbar-tool-tooltip">Избранное</span>
                                    </a>
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
                            { !hide_search_form && (
                                <form className="input-group d-lg-none my-3" action="/search/">
                                    <i className="ci-search position-absolute top-50 start-0 translate-middle-y ms-3" />
                                    <input
                                        className="form-control rounded-start"
                                        name="text"
                                        type="text"
                                        placeholder="Поиск товаров"
                                        autoComplete="off"
                                        value={searchText}
                                        onChange={(e) => setSearchText(e.target.value)} />
                                </form>
                            )}
                            <ul className="navbar-nav pe-lg-2 me-lg-2">
                                <li className="nav-item">
                                    <button ref={catalogButtonRef}
                                        className="btn btn-primary fw-bold w-100 text-start text-lg-center dropdown-toggle"
                                        onClick={() => setCatalogVisible(!catalogVisible)}>
                                        <i className={(catalogVisible ? "ci-close" : "ci-menu") + " align-middle mt-n1 me-2"} />Каталог
                                    </button>
                                </li>
                            </ul>
                            <ul className="navbar-nav d-lg-flex">
                                { /* <li class="nav-item"><a class="nav-link" href="{% url 'sales_actions' %}">Акции</a></li> */ }
                                <li className="nav-item">
                                    <Link href="/pages/articles/">
                                        <a className="nav-link">Справочные материалы</a>
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
                                <li className="nav-item dd-md-none"><a className="nav-link" href="'stores'">Магазины</a></li>
                                <li className="nav-item"><a className="nav-link" href="'service'">Сервисные центры</a></li>
                                <li className="nav-item">
                                    <Link href="/pages/delivery/">
                                        <a className="nav-link">Доставка и оплата</a>
                                    </Link>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <Catalog visible={catalogVisible} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} />
        </>
    )
};
