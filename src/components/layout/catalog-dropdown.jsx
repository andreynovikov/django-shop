import { useRef, useEffect } from 'react'
import { useRouter } from 'next/router'

import Catalog from '@/components/catalog'

export default function CatalogDropDown({ visible, setVisible, buttonRef }) {
    const ref = useRef()

    const router = useRouter()

    useEffect(() => {
        const handleRouteChange = () => {
            setVisible(false)
        }
        router.events.on('routeChangeStart', handleRouteChange)
        return () => {
            router.events.off('routeChangeStart', handleRouteChange)
        }
    }, [router.events, setVisible])

    useEffect(() => {
        function handleClickOutside(event) {
            if (!ref.current?.contains(event.target) && !buttonRef.current?.contains(event.target)) {
                setVisible(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => {
            document.removeEventListener("mousedown", handleClickOutside)
        }
    }, [setVisible])

    return (
        <div className={"position-relative" + (visible ? "" : " d-none")} ref={ref}>
            <div className="sw-catalog-dropdown">
                <Catalog />
            </div>
        </div>
    )
}