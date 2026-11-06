export function Loading({ className, mega = false }: { className?: string, mega?: boolean }) {
  return (
    <div className={className}>
      <div className="spinner-border" role="status" style={mega ? { width: "5rem", height: "5rem" } : {}}>
        <span className="visually-hidden">Загружается...</span>
      </div>
    </div>
  )
}

export function PageLoading({ className }: { className?: string }) {
  return (
      <div className="container">
        <div className={className}>
          <Loading className="text-center my-5 py-5" mega />
        </div>
      </div>
  )
}

export function ButtonLoading() {
  return <span className="spinner-border spinner-border-sm" style={{ marginLeft: "0.5rem" }} />
}