'use client'

import { useRef, useEffect, RefObject, Dispatch, SetStateAction, ReactNode } from 'react'

import { useNavigation } from '@/lib/navigation'

interface CatalogDropDownProps {
  catalog: ReactNode
  visible: boolean
  setVisible: Dispatch<SetStateAction<boolean>>
  buttonRef: RefObject<HTMLButtonElement | null>
}

export default function CatalogDropDown({ catalog, visible, setVisible, buttonRef }: CatalogDropDownProps) {
  const ref = useRef<HTMLDivElement>(null)

  const { path } = useNavigation()

  useEffect(() => {
      setVisible(false)
  }, [path, setVisible])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target

      if (!(target instanceof Node) || (!ref.current?.contains(target) && !buttonRef.current?.contains(target))) {
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
        {catalog}
      </div>
    </div>
  )
}