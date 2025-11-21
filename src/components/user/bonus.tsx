import { useQuery } from '@tanstack/react-query'

import OverlayTrigger from 'react-bootstrap/OverlayTrigger'
import Tooltip from 'react-bootstrap/Tooltip'

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
    <OverlayTrigger overlay={<Tooltip>Накопленные бонусы</Tooltip>} placement="right">
      <div className={`d-flex align-items-center gap-2 badge ${bonus.is_fresh ? 'bg-warning' : bonus.is_undefined ? 'bg-danger' : 'bg-dark'} position-absolute end-0 mt-n2`}>
        {bonus.value}
        {(isFetching || bonus.is_updating) && <span className="spinner-border" style={{ width: "0.5rem", height: "0.5rem" }} role="status" aria-hidden="true" />}
      </div>
    </OverlayTrigger>
  )
}