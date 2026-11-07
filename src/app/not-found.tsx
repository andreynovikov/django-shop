import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Страница не найдена',
}

export default function NotFound() {
  return (
    <div className="m-12 text-center">
      <div className="text-3xl">К сожалению, запрашиваемая вами страница не найдена</div>
      <div className="mt-12 text-[10rem] text-gray-200">404</div>
    </div>
  )
}