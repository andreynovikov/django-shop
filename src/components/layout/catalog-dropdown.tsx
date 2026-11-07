'use client'

import { useRef, useEffect, RefObject, Dispatch, SetStateAction, ReactNode } from 'react'
import { usePathname } from 'next/navigation'

interface CatalogDropDownProps {
  catalog: ReactNode
  visible: boolean
  setVisible: Dispatch<SetStateAction<boolean>>
  buttonRef: RefObject<HTMLButtonElement | null>
}

export default function CatalogDropDown({ catalog, visible, setVisible, buttonRef }: CatalogDropDownProps) {
  const ref = useRef<HTMLDivElement>(null)

  const pathname = usePathname()

  useEffect(() => {
      setVisible(false)
  }, [pathname, setVisible])

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
    <div className={`relative ${visible ? '' : 'hidden'}`} ref={ref}>
      <div className="bg-white py-5 md:absolute md:top-[.78125rem] md:z-995 md:min-w-[48rem] md:rounded-b-md md:border md:border-t-0 md:border-black/[.085] md:px-5 md:shadow-[0_1rem_1rem_rgb(0_0_0/.15)] lg:min-w-[50rem]">
        {catalog}
      </div>
    </div>
  )
}