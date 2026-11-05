'use client'

import { createContext, ReactNode, useContext, useMemo, useState } from 'react'

import { Tabs } from '@base-ui/react/tabs'

type ProductTabsContextType = {
  tab: string
  setTab: (tab: string) => void
}

const ProductTabsContext = createContext<ProductTabsContextType>({ tab: '', setTab: () => { } })

export function useProductTabs() {
  return useContext(ProductTabsContext)
}

// Holds the current tab, so the rating link above the tabs can open the reviews
export function ProductTabsProvider({ defaultTab, children }: { defaultTab: string, children: ReactNode }) {
  const [tab, setTab] = useState(defaultTab)
  const value = useMemo(() => ({ tab, setTab }), [tab])

  return (
    <ProductTabsContext.Provider value={value}>{children}</ProductTabsContext.Provider>
  )
}

export type ProductTab = {
  value: string
  label: string
  content: ReactNode
}

export const productTabsId = 'product-tabs'

const tabClassName = (state: Tabs.Tab.State) => 'nav-link detail-nav-link' + (state.active ? ' active' : '')

// Panels are rendered on the server and kept in the page, the hidden ones too
export function ProductTabs({ tabs }: { tabs: ProductTab[] }) {
  const { tab, setTab } = useProductTabs()

  return (
    <Tabs.Root id={productTabsId} value={tab} onValueChange={(value) => setTab(value)}>
      <Tabs.List className="nav nav-tabs flex-column flex-sm-row">
        {tabs.map(({ value, label }) => (
          <Tabs.Tab className={tabClassName} value={value} key={value}>
            {label}
          </Tabs.Tab>
        ))}
      </Tabs.List>
      {tabs.map(({ value, content }) => (
        <Tabs.Panel className="py-3" value={value} keepMounted key={value}>
          {content}
        </Tabs.Panel>
      ))}
    </Tabs.Root>
  )
}
