import { useQuery } from '@tanstack/react-query'

import Tooltip from '@/components/ui/tooltip'
import { badgeClass } from '@/components/ui/badge'
import { Spinner } from '@/components/loading'

import { useSession } from '@/lib/session'
import { userKeys, getUserBonus } from '@/lib/queries'

import { UserBonus as UserBonusType } from '@/lib/types'

export default function UserBonus() {
  const { status } = useSession()

  const { data: bonus, isFetching, isLoading } = useQuery<UserBonusType>({
    queryKey: userKeys.bonus(),
    queryFn: () => getUserBonus(),
    enabled: status === 'authenticated',
    refetchInterval: (query) => query.state.data?.is_updating ? 1000 : false
  })

  if (status !== 'authenticated' || isLoading || bonus === undefined)
    return null

  return (
    <Tooltip content="Накопленные бонусы" side="right">
      <div className={`${badgeClass()} absolute right-0 -mt-2 flex! items-center gap-2 text-white ${bonus.is_fresh ? 'bg-warning' : bonus.is_undefined ? 'bg-danger' : 'bg-dark'}`}>
        {bonus.value}
        {(isFetching || bonus.is_updating) && <Spinner size="xs" />}
      </div>
    </Tooltip>
  )
}