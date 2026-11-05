'use client'

import { useSyncExternalStore } from 'react'
import { useRouter } from 'next/navigation'

import { IconScale } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'

import useComparison from '@/lib/comparison'

const subscribeNothing = () => () => {}

// Adds the product to the comparison, or opens the comparison of its kind when it is already there
export default function ProductCompareButton({ productId, kind }: { productId: number, kind: number }) {
  const router = useRouter()
  const { comparisons, compare } = useComparison()

  // The server renders the button with no comparisons. The header may load them before this part of the page is
  // hydrated, the compared state would then not match the server HTML, so it is shown once the button is hydrated.
  const hydrated = useSyncExternalStore(subscribeNothing, () => true, () => false)
  const compared = hydrated && comparisons.includes(productId)

  const handleClick = () => {
    if (compared)
      router.push(`/compare/?kind=${kind}`)
    else
      compare(productId)
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className={`${buttonClass({ variant: 'outline-secondary' })} mb-1`}>
      <IconScale className="me-2" />
      <span>
        {compared ? "Сравнение" : "Добавить в сравнение"}
      </span>
    </button>
  )
}
