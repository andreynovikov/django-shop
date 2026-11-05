'use client'

import { useRouter } from 'next/navigation'

import { IconScale } from '@tabler/icons-react'

import { buttonClass } from '@/components/ui/button'

import useComparison from '@/lib/comparison'

// Adds the product to the comparison, or opens the comparison of its kind when it is already there
export default function ProductCompareButton({ productId, kind }: { productId: number, kind: number }) {
  const router = useRouter()
  const { comparisons, compare } = useComparison()

  const compared = comparisons.includes(productId)

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
