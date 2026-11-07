'use client'

import { useEffect } from 'react'

export default function Error({ error }: { error: unknown }) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return <div className="m-12 text-center">
    <div className="text-3xl">К сожалению, что-то пошло не так</div>
    <div className="mt-1 text-xl font-light">Мы постараемся исправить это как можно скорее</div>
    <div className="mt-12 text-[10rem] text-gray-200">500</div>
  </div>
}