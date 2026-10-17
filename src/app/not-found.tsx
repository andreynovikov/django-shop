import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Страница не найдена',
}

export default function NotFound() {
  return (
    <div className="m-5 text-center">
      <div className="fs-2">К сожалению, запрашиваемая вами страница не найдена</div>
      <div className="mt-5 text-secondary" style={{ fontSize: "10rem" }}>404</div>
    </div>
  )
}