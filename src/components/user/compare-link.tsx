import { IconRepeat } from '@tabler/icons-react'

import { badgeClass } from '@/components/ui/badge'

import useComparison from '@/lib/comparison'

export default function CompareLink({ mobile = false }: { mobile?: boolean }) {
  const { comparisons } = useComparison()

  return (
    <>
      <IconRepeat size="1.15em" stroke={1.5} className={`-mt-1 align-middle ${mobile ? 'me-2 text-muted' : 'me-1.5 text-primary'}`} />
      Сравнение
      {comparisons.length > 0 && (
        <span className={`${badgeClass({ pill: true })} ms-1 bg-primary text-white`}>{comparisons.length}</span>
      )}
    </>
  )
}
