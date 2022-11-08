import { signOut } from '@/lib/session';

export default function TopSidebar({ children }) {
    return (
        <div className="d-none d-lg-flex justify-content-between align-items-center pt-lg-3 pb-4 pb-lg-5 mb-lg-3">
            { children }
            <button className="btn btn-primary btn-sm" type="button" onClick={() => signOut({callbackUrl: '/'})}>
                <i className="ci-sign-out me-2" />Выход
            </button>
        </div>
    )
}
