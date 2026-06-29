import Spinner from 'react-bootstrap/Spinner'

export function Loading({ className, mega = false }) {
  return (
    <div className={className}>
      <Spinner animation="border" role="status" style={mega ? { width: "5rem", height: "5rem" } : {}}>
        <span className="visually-hidden">Загружается...</span>
      </Spinner>
    </div>
  )
}

export function PageLoading({ className }) {
  return (
      <div className="container">
        <div className={className}>
          <Loading className="text-center my-5 py-5" mega />
        </div>
      </div>
  )
}

export function ButtonLoading() {
  return <Spinner animation="border" size="sm" style={{ marginLeft: "0.5rem" }} />
}