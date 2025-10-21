import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'

import { IconCategory, IconX } from '@tabler/icons-react'

import Collapse from 'react-bootstrap/Collapse'

import CartNotice from '@/components/cart/notice'
import OrderTracking from '@/components/order/tracking'
import CompareLink from '@/components/user/compare-link'
import UserProfileLink from '@/components/user/profile-link'
import ProductSearchInput from '@/components/product/search-input'

import CatalogDropDown from './catalog-dropdown'

import useComparison from '@/lib/comparison'
import useFavorites from '@/lib/favorites'
import { useSite } from '@/lib/site'
import { useSession } from '@/lib/session'
import { formatPhone } from '@/lib/format'

export default function TopBar({ hideSignIn, hideCartNotice, topMenuOpen, toggleTopMenu }) {
    const [catalogVisible, setCatalogVisible] = useState(false)
    const { site } = useSite()
    const { status } = useSession()

    const stuckMenuRef = useRef()
    const catalogButtonRef = useRef()

    /*
    useEffect(() => {
        const topbar = document.querySelector('.topbar')

        if (catalogVisible) {
            if (window.innerWidth > 992 && window.pageYOffset > topbar.offsetHeight) { // lg
                window.scrollTo(0, topbar.offsetHeight)
            }
        }

        const setStickyState = (event) => {
            const navbar = document.querySelector('.navbar-sticky')
            const navbarHeight = navbar.offsetHeight
            if (event.currentTarget.pageYOffset > topbar.offsetHeight && !catalogVisible) {
                //document.body.style.paddingTop = navbarHeight + 'px'
                navbar.classList.add('navbar-stuck')
            } else {
                document.body.style.paddingTop = ''
                navbar.classList.remove('navbar-stuck')
            }
        }

        window.addEventListener('scroll', setStickyState)

        return () => {
            window.removeEventListener('scroll', setStickyState)
        }
    }, [catalogVisible])
    */

    const handleStuckToggler = () => {
        stuckMenuRef.current?.classList.toggle('show')
    }

    const { comparisons } = useComparison()
    const { favorites } = useFavorites()

    const seoLogoAlt = "Швейный Мир - всероссийская сеть швейных супермаркетов.&#10; Швейные машинки, вышивальные и вязальные машины, оверлоки и аксессуары."

    return (
        <>
            <div className="navbar-sticky-turned-off bg-light">
            <div className="topbar topbar-light sw-bg-light">
                <div className="container">
                    <div className="d-flex flex-grow-1 justify-content-between d-md-inline-block">
                        {site.phone && (
                            <div className="topbar-text text-nowrap">
                                <i className="ci-support mt-n1" />
                                <a className="topbar-link" href={"tel:" + "+74957440087"}>{formatPhone("+74957440087")}</a>
                                <span className="text-muted d-none d-lg-inline">&nbsp;&ndash;&nbsp;розничные магазины</span>
                            </div>
                        )}
                        {site.phone && (
                            <div className="topbar-text text-nowrap border-start ps-md-3 ms-md-3">
                                <i className="ci-support mt-n1" />
                                <a className="topbar-link" href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
                                <span className="text-muted d-none d-lg-inline">&nbsp;&ndash;&nbsp;интернет-магазин</span>
                            </div>
                        )}
                    </div>
                    <div className="d-none d-md-inline-block">
                        {comparisons.length > 0 && (
                            <Link className="topbar-link text-nowrap border-end pe-3 me-3" href="/compare" rel="nofollow">
                                <CompareLink />
                            </Link>
                        )}
                        <OrderTracking />
                    </div>
                </div>
            </div>
                <div className="navbar navbar-expand-lg navbar-light">
                    <div className="container">
                        <Link className="navbar-brand flex-shrink-0" href="/">
                            <img src="/i/logo.svg" alt={seoLogoAlt} />
                        </Link>
                        <div className="d-none d-lg-flex w-100 mx-4">
                            <ProductSearchInput />
                        </div>
                        <div className="d-none d-md-flex d-lg-none flex-grow-1 mx-2">
                            <ProductSearchInput mobile />
                        </div>
                        <div className="navbar-toolbar d-flex flex-shrink-0 align-items-center">
                            <button className="navbar-toggler" type="button" onClick={toggleTopMenu}>
                                <span className="navbar-toggler-icon"></span>
                            </button>
                            <button className="btn p-0 navbar-tool navbar-stuck-toggler" onClick={handleStuckToggler}>
                                <span className="navbar-tool-tooltip">Раскрыть меню</span>
                                <div className="navbar-tool-icon-box"><i className="navbar-tool-icon ci-menu" /></div>
                            </button>
                            {status === 'authenticated' && (
                                <Link className="navbar-tool d-none d-lg-flex" href="/user/favorites">
                                    <div className="navbar-tool-icon-box">
                                        {favorites.length > 0 && <span className="navbar-tool-label">{favorites.length}</span>}
                                        <i className="navbar-tool-icon ci-heart" />
                                    </div>
                                    <span className="navbar-tool-tooltip">Избранное</span>
                                </Link>
                            )}
                            {!hideSignIn && <UserProfileLink />}
                            {!hideCartNotice && <CartNotice />}

                        </div>
                    </div>
                </div>
                <div className="navbar navbar-expand-lg navbar-light navbar-stuck-menu mt-n2 pt-0 pb-2" ref={stuckMenuRef}>
                    <div className="container">
                        <div className="flex-grow-1 d-md-none my-3">
                            <ProductSearchInput mobile />
                        </div>
                        <Collapse in={topMenuOpen} className="navbar-collapse">
                            <div>
                                <ul className="navbar-nav pe-lg-2 me-lg-2">
                                    <li className="nav-item bg-transparent">
                                        <button ref={catalogButtonRef}
                                            className="btn btn-primary w-100 fw-bold text-start text-lg-center dropdown-toggle"
                                            onClick={() => setCatalogVisible(!catalogVisible)}>
                                            <span className="me-2 align-text-bottom">
                                                {catalogVisible ? <IconX strokeWidth={1.5} /> : <IconCategory strokeWidth={1.5} />}
                                            </span>
                                            Каталог
                                        </button>
                                        <CatalogDropDown visible={catalogVisible} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} />
                                    </li>
                                </ul>
                                <ul className="navbar-nav">
                                    <li className="nav-item">
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
                                            Доставка
                                        </Link>
                                    </li>
                                    <li className="nav-item d-md-none">
                                        <Link className="nav-link" href="/user/orders?track" rel="nofollow">
                                            Отслеживание заказа
                                        </Link>
                                    </li>
                                </ul>
                            </div>
                        </Collapse>
                    </div>
                </div>
            </div>
        </>
    )
}
