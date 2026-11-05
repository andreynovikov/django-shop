import { Spinner } from '@/components/loading'

// The spinner shown while a page is rendered on its first visit
export default function LoadingMessage() {
  return (
    <div className="container my-12 flex items-center justify-center text-secondary">
      <Spinner className="mx-4" />
      <strong>Загружается...</strong>
    </div>
  )
}
