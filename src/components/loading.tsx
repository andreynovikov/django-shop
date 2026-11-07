const spinnerSizes = {
  xs: 'size-2 border-2',
  sm: 'size-4 border-2',
  md: 'size-8 border-4',
  lg: 'size-20 border-4',
}

// A spinning ring in the text color, announced when it has a label
export function Spinner({ size = 'md', label, className = '' }: { size?: keyof typeof spinnerSizes, label?: string, className?: string }) {
  return (
    <span
      className={`inline-block shrink-0 animate-spin rounded-full border-current border-e-transparent align-[-0.125em] ${spinnerSizes[size]} ${className}`}
      role={label ? 'status' : undefined}
      aria-hidden={label ? undefined : true}>
      {label && <span className="sr-only">{label}</span>}
    </span>
  )
}

export function Loading({ className, mega = false }: { className?: string, mega?: boolean }) {
  return (
    <div className={className}>
      <Spinner size={mega ? 'lg' : 'md'} label="Загружается..." />
    </div>
  )
}

export function PageLoading({ className }: { className?: string }) {
  return (
      <div className="container">
        <div className={className}>
          <Loading className="my-12 py-12 text-center" mega />
        </div>
      </div>
  )
}

export function ButtonLoading() {
  return <Spinner size="sm" className="ms-2" />
}
