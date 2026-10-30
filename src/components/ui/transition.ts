type TransitionStatus = 'starting' | 'ending' | 'idle' | undefined

// Bootstrap .show is toggled after a Base UI popup is mounted and before it is unmounted, so Bootstrap transitions run both ways
export const shown = ({ transitionStatus }: { transitionStatus: TransitionStatus }) =>
  transitionStatus !== 'starting' && transitionStatus !== 'ending'
