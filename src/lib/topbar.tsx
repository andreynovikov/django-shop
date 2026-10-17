import { useState, useEffect, createContext, useContext, Dispatch, SetStateAction, ReactNode, useCallback } from 'react'

interface TopbarContextType {
  hideSignIn: boolean
  hideCartNotice: boolean
  topMenuOpen: boolean
  setHideSignIn: Dispatch<SetStateAction<boolean>>
  setHideCartNotice: Dispatch<SetStateAction<boolean>>
  setTopMenuOpen: Dispatch<SetStateAction<boolean>>
  toggleTopMenu: () => void
}

export const TopbarContext = createContext<TopbarContextType | null>(null)

export function useTopbar() {
  const context = useContext(TopbarContext)

  if (!context)
    throw new Error('useCustomizeTopbar must be used within a TopbarProvider')

  const { hideSignIn, hideCartNotice, topMenuOpen, setTopMenuOpen, toggleTopMenu } = context
  return { hideSignIn, hideCartNotice, topMenuOpen, setTopMenuOpen, toggleTopMenu }
}

export function useCustomizeTopbar({ 
  hideSignIn, 
  hideCartNotice 
}: {
  hideSignIn?: boolean, 
  hideCartNotice?: boolean, 
}) {
  const context = useContext(TopbarContext)

  if (!context)
    throw new Error('useCustomizeTopbar must be used within a TopbarProvider')

  useEffect(() => {
    if (hideSignIn !== undefined && hideSignIn !== context.hideSignIn)
      context.setHideSignIn(hideSignIn)
    if (hideCartNotice !== undefined && hideCartNotice !== context.hideCartNotice)
      context.setHideCartNotice(hideCartNotice)
  }, [hideSignIn, hideCartNotice, context])
}


interface TopbarProviderProps {
  children: ReactNode;
}

export function TopbarProvider({ children }: TopbarProviderProps) {
  const [hideSignIn, setHideSignIn] = useState(false)
  const [hideCartNotice, setHideCartNotice] = useState(false)
  const [topMenuOpen, setTopMenuOpen] = useState(false)

  const toggleTopMenu = useCallback(() => setTopMenuOpen((open) => !open), [setTopMenuOpen])

  const context = {
    hideSignIn,
    hideCartNotice,
    topMenuOpen,
    setHideSignIn,
    setHideCartNotice,
    setTopMenuOpen,
    toggleTopMenu
  }

  return (
    <TopbarContext.Provider value={context}>{children}</TopbarContext.Provider>
  )
}