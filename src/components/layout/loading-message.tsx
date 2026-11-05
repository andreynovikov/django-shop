// The spinner shown while a page is rendered on its first visit
export default function LoadingMessage() {
  return (
    <div className="container d-flex align-items-center justify-content-center text-secondary my-5">
      <div className="spinner-border mx-3" role="status" aria-hidden="true"></div>
      <strong>Загружается...</strong>
    </div>
  )
}
