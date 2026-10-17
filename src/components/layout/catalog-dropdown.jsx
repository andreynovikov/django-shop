'use client'

import { useRef, useEffect } from 'react'

import Catalog from '@/components/catalog'

import { useNavigation } from '@/lib/navigation'

export default function CatalogDropDown({ visible, setVisible, buttonRef }) {
  const ref = useRef()

  const { path } = useNavigation()

  useEffect(() => {
      setVisible(false)
  }, [path, setVisible])

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
  }, [buttonRef, setVisible])

  return (
    <div className={"position-relative" + (visible ? "" : " d-none")} ref={ref}>
      <div className="sw-catalog-dropdown">
        <Catalog />
      </div>
    </div>
  )
}