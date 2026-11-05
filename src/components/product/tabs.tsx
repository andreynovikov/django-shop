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

const tabClassName = (state: Tabs.Tab.State) => '-mb-px border-b px-6 py-4 text-[.8rem] font-bold tracking-widest uppercase transition-colors hover:border-b-dark hover:text-dark focus-visible:border-b-dark focus-visible:text-dark focus-visible:outline-none ' +
  (state.active ? 'border-b-dark text-dark' : 'border-b-[#ddd] text-gray-600')

// Panels are rendered on the server and kept in the page, the hidden ones too
export function ProductTabs({ tabs }: { tabs: ProductTab[] }) {
  const { tab, setTab } = useProductTabs()

  return (
    <Tabs.Root id={productTabsId} value={tab} onValueChange={(value) => setTab(value)}>
      <Tabs.List className="flex flex-col border-b sm:flex-row sm:flex-wrap">
        {tabs.map(({ value, label }) => (
          <Tabs.Tab className={tabClassName} value={value} key={value}>
            {label}
          </Tabs.Tab>
        ))}
      </Tabs.List>
      {tabs.map(({ value, content }) => (
        <Tabs.Panel className="py-4" value={value} keepMounted key={value}>
          {content}
        </Tabs.Panel>
      ))}
    </Tabs.Root>
  )
}
