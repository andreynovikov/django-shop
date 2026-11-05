import { Spinner } from '@/components/loading'

export default function Loading() {
  return (
    <div className="my-12 flex items-center justify-center px-3 text-secondary">
      <Spinner className="mx-4" />
      <strong>Загружается...</strong>
    </div>
  )
}
