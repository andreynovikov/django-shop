import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'

import { IconCategory, IconX } from '@tabler/icons-react'

import { Menu } from '@base-ui/react/menu'
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

  const navbarRef = useRef()
  const stickyRef = useRef()
  const stuckMenuRef = useRef()
  const catalogButtonRef = useRef()

  useEffect(() => {
    if (catalogVisible) {
      if (window.innerWidth > 992 /* lg */ && navbarRef.current?.classList.contains('sw-sticky')) {
        window.scrollTo(0, 0)
      }
    }
    stickyRef.current?.classList.toggle('sw-sticky', !catalogVisible)

    const setNavbarState = (event) => {
      const headerHeight = (navbarRef.current?.offsetHeight ?? 0) - 15
      const offset = (stickyRef.current?.getBoundingClientRect().bottom ?? 0) + event.currentTarget.pageYOffset
      if (offset >= headerHeight && !navbarRef.current?.classList.contains('sw-sticky') && !catalogVisible) {
        navbarRef.current?.classList.remove('show')
        navbarRef.current?.classList.add('sw-sticky')
      } else if (offset < headerHeight && navbarRef.current?.classList.contains('sw-sticky')) {
        navbarRef.current?.classList.remove('sw-sticky')
      }
    }

    window.addEventListener('scroll', setNavbarState)

    return () => {
      window.removeEventListener('scroll', setNavbarState)
    }
  }, [catalogVisible])

  const handleStuckToggler = () => {
    navbarRef.current?.classList.toggle('show')
  }

  const { comparisons } = useComparison()
  const { favorites } = useFavorites()

  const seoLogoAlt = "Janome.Club - Фирменный магазин Janome. Швейные машины, вышивальные машины, оверлоки и аксессуары."

  return (
    <div className="sw-navbar" ref={navbarRef}>
      <div className="sw-navbar-sticky bg-light" ref={stickyRef}>
        <div className="topbar topbar-light sw-bg-light">
          <div className="container">
            <div className="d-flex flex-grow-1 justify-content-between d-md-inline-block">
              <Menu.Root>
                <Menu.Trigger className="d-lg-none topbar-text text-nowrap sw-with-caret" nativeButton={false} render={<div />}>
                  <i className="ci-support mt-n1" />
                  Телефоны
                </Menu.Trigger>
                <Menu.Portal>
                  <Menu.Positioner sideOffset={8}>
                    <Menu.Popup className="dropdown-menu position-static topbar flex-column align-items-start gap-2 p-3">
                      <div className="topbar-text text-nowrap">
                        <a className="topbar-link" href={"tel:" + "+74957440087"}>{formatPhone("+74957440087")}</a>
                        <span className="text-muted">&nbsp;&ndash;&nbsp;Магазин на Автозаводской</span>
                      </div>
                      {site.phone && (
                        <div className="topbar-text text-nowrap">
                          <a className="topbar-link" href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
                          <span className="text-muted">&nbsp;&ndash;&nbsp;Интернет-магазин</span>
                        </div>
                      )}
                    </Menu.Popup>
                  </Menu.Positioner>
                </Menu.Portal>
              </Menu.Root>
              <div className={"d-none d-lg-inline-block topbar-text text-nowrap" + (site.phone ? " border-end pe-3 me-3" : "")}>
                <i className="ci-support mt-n1" />
                <a className="topbar-link" href={"tel:" + "+74957440087"}>{formatPhone("+74957440087")}</a>
                <span className="text-muted d-none d-lg-inline">&nbsp;&ndash;&nbsp;Магазин на Автозаводской</span>
              </div>
              {site.phone && (
                <div className="d-none d-lg-inline-block topbar-text text-nowrap">
                  <i className="ci-support mt-n1" />
                  <a className="topbar-link" href={"tel:" + site.phone}>{formatPhone(site.phone)}</a>
                  <span className="text-muted d-none d-lg-inline">&nbsp;&ndash;&nbsp;Интернет-магазин</span>
                </div>
              )}
              <div className={"d-none d-md-inline-block d-lg-none" + (site.phone ? " border-start ps-3 ms-3" : "")} style={{ width: 0 }}>&nbsp;</div>
              <div className="d-lg-none topbar-text text-nowrap">
                <i className="ci-location mt-n1" />
                <Link className="topbar-link" href="/stores/">
                  Магазины
                </Link>
              </div>
            </div>
            <div className="d-none d-md-inline-block">
              {comparisons.length > 0 && (
                <Link className="topbar-link text-nowrap" href="/compare" rel="nofollow">
                  <CompareLink />
                </Link>
              )}
              <OrderTracking addDivider={comparisons.length > 0} />
            </div>
          </div>
        </div>
        <div className="navbar navbar-expand-lg navbar-light">
          <div className="container">
            <Link className="navbar-brand flex-shrink-0" href="/">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              {/*<img src="/i/logo.svg" alt={seoLogoAlt} />*/}
              <svg xmlns="http://www.w3.org/2000/svg" width="275" height="48" viewBox="0 0 286 50" alt={seoLogoAlt}>
                <path fill="#df0623" d="M6.43156839,34.5465984 L5.75423089,33.440649 L0,37.7880767 L0.308340867,38.520795 C1.76723961,41.5061228 3.97843684,43.8380735 7.03185034,45.5261562 C10.1538014,47.2068842 13.7125242,48 17.6830255,48 C22.7185736,47.9381168 26.4486038,46.5120535 29.021636,43.5761283 C31.714576,40.5871604 33,36.5562065 33,31.4833408 L33,0 L16.8950699,0 L16.8950699,30.3097136 C16.8358076,32.7785058 16.5253721,34.6098931 15.9172419,35.7616791 C15.2484662,36.945484 14.2613193,37.6025012 12.8545314,37.8477312 C12.3670371,37.9932646 11.9966113,37.9932646 11.7497336,37.9932646 C10.2315558,37.9932646 8.81479373,37.2641864 7.46937938,35.8380488 L6.43156839,34.5465984 Z M63.2796736,1 L51.4483633,1 L33,48 L45.6978994,48 L47.8342712,41.5253192 L63.1688172,41.5253192 L65.3153199,48 L81,48 L63.2796736,1 Z M56.0580147,20 L60,33 L52,33 L56.0580147,20 Z M91.7682195,1 L82,1 L82,48 L93.5142504,48 L93.5142504,24.1350158 L114.72899,48 L123,48 L123,1 L111.483611,1 L111.427287,23.2794319 L91.7682195,1 Z M168.471463,6.39340426 C164.113352,2.12423464 158.367261,0 151.218808,0 C143.966796,0 138.283273,2.3880659 134.048857,7.16087113 C129.999266,11.834093 128,17.7751484 128,25.1181186 C128.05178,31.9768608 130.117208,37.4696989 134.28618,41.6724182 C138.522753,45.9510701 143.966796,48 150.735533,48 C158.121309,47.9385306 163.998286,45.7465166 168.344891,41.2748965 C172.820944,36.7650518 175,30.8183144 175,23.4585932 C175,16.3447495 172.820944,10.6525971 168.471463,6.39340426 Z M157.243905,34.5373646 C156.020699,36.8682727 154.192158,38 151.729028,38 C149.38989,38 147.694397,36.8071273 146.634192,34.4180129 C145.517564,32.0344896 145,28.0839815 145,22.5593917 C145.05712,17.9782187 145.64086,14.7179437 146.817395,12.7134072 C147.919395,10.8768951 149.564036,10 151.785451,10 C154.192158,10.0715394 155.954523,11.0039886 157.131058,12.9571286 C158.414867,14.9628837 159,18.2253808 159,22.8710683 C159,28.3204629 158.414867,32.2240188 157.243905,34.5373646 Z M196.403879,1 L182.557039,1 L176,48 L187.980817,48 L190.46242,23.8761736 L199.011565,47.9371016 L208.748853,47.9371016 L217.606529,23.8097263 L220.275773,48 L235,48 L228.144071,1 L214.610212,1 L205.305314,25.9890452 L196.403879,1 Z M273.398615,1 L241,1 L241,48 L275,48 L275,37.6205614 L256.565633,37.6205614 L256.565633,28.6293419 L270.472435,28.6293419 L270.472435,19.0448541 L256.565633,19.0448541 L256.565633,11.5147946 L273.398615,11.5147946 L273.398615,1 Z" />
              </svg>
            </Link>
            <div className="d-none d-md-flex w-lg-100 flex-grow-1 mx-2 mx-lg-4">
              <ProductSearchInput />
            </div>
            <div className="navbar-toolbar d-flex flex-shrink-0 align-items-center">
              <button className="navbar-toggler d-md-none" type="button" onClick={toggleTopMenu}>
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
      </div>
      <div className="navbar navbar-expand-md navbar-light navbar-stuck-menu bg-light pt-0 pb-2" ref={stuckMenuRef}>
        <div className="container">

          <div className="d-flex gap-2">
            <ul className="navbar-nav pe-lg-2 me-lg-2 my-3 my-lg-0">
              <li className="nav-item bg-transparent mb-0">
                <button ref={catalogButtonRef}
                  className="btn btn-secondary w-100 text-start text-lg-center dropdown-toggle"
                  style={{ fontSize: "1rem" }}
                  onClick={() => setCatalogVisible(!catalogVisible)}>
                  <span className="me-2 align-text-bottom d-none d-md-inline">
                    {catalogVisible ? <IconX strokeWidth={1.5} /> : <IconCategory strokeWidth={1.5} />}
                  </span>
                  Каталог
                </button>
                <CatalogDropDown visible={catalogVisible} setVisible={setCatalogVisible} buttonRef={catalogButtonRef} />
              </li>
            </ul>
            {!catalogVisible && <div className="flex-shrink-1 d-md-none my-3">
              <ProductSearchInput mobile />
            </div>}
          </div>

          <Collapse in={topMenuOpen} className="navbar-collapse">
            <div>
              <ul className="navbar-nav">
                <li className="nav-item">
                  <Link className="nav-link" href="/stores/">
                    Магазин на Автозаводской
                  </Link>
                </li>
                <li className="nav-item">
                  <Link className="nav-link" href="/pages/delivery/">
                    Доставка
                  </Link>
                </li>
                <li className="nav-item d-md-none">
                  <Link className="nav-link" href="/user/orders?track" rel="nofollow">
                    Состояние заказа
                  </Link>
                </li>
              </ul>
            </div>
          </Collapse>
        </div>
      </div>
    </div>
  )
}
