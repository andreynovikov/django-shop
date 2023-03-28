import Link from 'next/link';

import { MobileCartNotice } from '@/components/cart/notice';

import useFavorites from '@/lib/favorites';
import { useSession } from '@/lib/session';

export default function HandheldBottomBar({hasSidebar=false}) {
    const { status } = useSession();
    const { favorites } = useFavorites();

    const handleMenuOpen = () => {
        window.scrollTo(0, 0);
    };

    return (
        <div className="handheld-toolbar">
            <div className="d-table table-layout-fixed w-100">
                { hasSidebar && (
                    <a class="d-table-cell handheld-toolbar-item" href="#" data-bs-toggle="offcanvas" data-bs-target="#shop-sidebar">
                        <span class="handheld-toolbar-icon"><i className="ci-filter-alt" /></span>
                        <span class="handheld-toolbar-label">Фильтры</span>
                    </a>
                )}
                { status === 'authenticated' && (
                    <Link className="d-table-cell handheld-toolbar-item" href="/user/favorites">
                        <span className="handheld-toolbar-icon">
                            <i className="ci-heart" />
                            { favorites.length > 0 && <span className="badge bg-primary rounded-pill ms-1">{ favorites.length }</span> }
                        </span>
                        <span className="handheld-toolbar-label">Избранное</span>
                    </Link>
                )}
                <a className="d-table-cell handheld-toolbar-item" data-bs-toggle="collapse" data-bs-target="#navbarCollapse" onClick={handleMenuOpen}>
                    <span className="handheld-toolbar-icon"><i className="ci-menu" /></span>
                    <span className="handheld-toolbar-label">Меню</span>
                </a>
                <MobileCartNotice />
            </div>
        </div>
    )
}
