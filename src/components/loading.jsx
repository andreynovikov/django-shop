import Spinner from 'react-bootstrap/Spinner'

export default function Loading({ className, mega = false }) {
  return (
    <div className={className}>
      <Spinner animation="border" role="status" style={mega ? { width: "5rem", height: "5rem" } : {}}>
        <span className="visually-hidden">Загружается...</span>
      </Spinner>
    </div>
  )
}
