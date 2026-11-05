'use client'

import LawOrionIcon from '@/components/law-orion-icon'
import useComparison from '@/lib/comparison'

export default function CompareLink() {
  const { comparisons } = useComparison()

  return (
    <>
      <LawOrionIcon className="svg-icon size-[25px]" />
      {comparisons.length > 0 && (
        <div className="absolute -top-1.25 -right-2 size-5 rounded-full bg-dark text-center text-[.6rem] leading-5 text-white">
          {comparisons.length}
        </div>
      )}
    </>
  )
}
