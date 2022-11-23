import Link from 'next/link';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faBars } from '@fortawesome/free-solid-svg-icons';

import SvgIcon from '@/components/svg-icon';
import CompareLink from '@/components/user/compare-link';

import { formatPhone } from '@/lib/format';
import useComparison from '@/lib/comparison';
import { useSession, signOut } from '@/lib/session';

export default function Header() {
    const { comparisons } = useComparison();
    const { user, status } = useSession();

    return (
        <header className="header">
            <nav className="navbar navbar-expand-lg navbar-sticky navbar-airy navbar-light bg-white bg-fixed-white">
                <div className="container-fluid">
                    <Link className="navbar-brand" href="/">
                        <img src="/i/logo.svg" alt="Швейная техника и аксессуары Family" className="img-responsive" />
                    </Link>
                    <button className="navbar-toggler navbar-toggler-right" type="button" data-bs-toggle="collapse" data-bs-target="#navbarCollapse"
                            aria-controls="navbarCollapse" aria-expanded="false" aria-label="Toggle navigation">
                        <FontAwesomeIcon icon={faBars} />
                    </button>
                    <div className="collapse navbar-collapse mt-2 mt-sm-0" id="navbarCollapse">
                        <ul className="navbar-nav mx-auto">
				            <li className="nav-item">
                                <Link className="nav-link" href="/catalog/sewing_machines">Швейные машины</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/catalog/overlock">Оверлоки</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/catalog/accessories">Аксессуары</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/news">Новости</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/pages/about">История</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/stores">Где купить</Link>
                            </li>
				            <li className="nav-item">
                                <Link className="nav-link" href="/service">Поддержка</Link>
                            </li>
                        </ul>
                        <div className="d-flex align-items-center justify-content-between justify-content-lg-end mt-1 mb-2 my-lg-0">
                            { comparisons.length > 0 && (
                                <div className="nav-item">
                                    <Link href="/compare" className="navbar-icon-link">
                                        <CompareLink />
                                    </Link>
                                </div>
                            )}
                            { /*
                                <div class="nav-item navbar-icon-link" data-bs-toggle="search">
                                <SvgIcon id="search-1" />
                                </div>
                              */
                            }
                            { status === 'authenticated' && (
                                <div className="nav-item dropdown">
                                    <a className="navbar-icon-link d-lg-none" onClick={signOut} style={{cursor:'pointer'}}>
                                        <SvgIcon id="male-user-1" className="svg-icon" />
                                        <span className="text-sm ms-2 ms-lg-0 text-uppercase text-sm fw-bold d-none d-sm-inline d-lg-none">Выйти</span>
                                    </a>
                                    <div className="d-none d-lg-block">
                                        <a className="navbar-icon-link" id="userdetails" data-bs-target="#" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                                            <SvgIcon id="male-user-1" className="svg-icon" />
                                        </a>
                                        <div className="dropdown-menu dropdown-menu-animated dropdown-menu-end p-4" aria-labelledby="userdetails">
                                            <div className="border-bottom mb-3">
                                                <strong className="text-uppercase text-nowrap">{ user?.name || formatPhone(user?.phone) }</strong>
                                            </div>
                                            <div className="d-flex justify-content-end">
                                                <a className="btn btn-outline-dark" onClick={signOut} style={{cursor:'pointer'}}>Выйти</a>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </nav>
            { /*
                <!-- Fullscreen search area-->
                <div class="search-area-wrapper">
                <div class="search-area d-flex align-items-center justify-content-center">
                <div class="close-btn">
                <SvgIcon id="close-1" class="svg-icon svg-icon-light w-3rem h-3rem" />
                </div>
                <form class="search-area-form" action="#">
                <div class="mb-4 position-relative">
                <input class="search-area-input" type="search" name="search" id="search" placeholder="What are you looking for?" />
                <button class="search-area-button" type="submit">
                <SvgIcon id="search-1" className="svg-icon" />
                </button>
                </div>
                </form>
                </div>
                </div>
              */
            }
        </header>
    )
}
