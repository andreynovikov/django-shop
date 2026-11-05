import { useState, useEffect, createContext, useContext, ReactElement, Dispatch, SetStateAction, ReactNode } from 'react'

interface ToolbarContextType {
  item: ReactElement | null
  setItem: Dispatch<SetStateAction<ReactElement | null>>
}

export const ToolbarContext = createContext<ToolbarContextType>({
  item: null,
  setItem: () => {}
})

export function useToolbar(toolbarItem?: ReactElement) {
  const { item, setItem } = useContext(ToolbarContext)
  useEffect(() => {
    if (toolbarItem === undefined)
      return
    setItem(toolbarItem)
    return () => setItem(null)
  }, [toolbarItem, setItem])
  return { item }
}

interface ToolbarProviderProps {
  children: ReactNode;
}

export function ToolbarProvider({ children } : ToolbarProviderProps) {
  const [item, setItem] = useState<ReactElement | null>(null)

  return (
    <ToolbarContext.Provider value={{ item, setItem }}>{children}</ToolbarContext.Provider>
  )
}
