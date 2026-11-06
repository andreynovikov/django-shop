'use client'

import { useEffect } from 'react'

export default function Error({ error }: { error: unknown }) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error)
  }, [error])

  return <div className="m-5 text-center">
    <div className="fs-2">К сожалению, что-то пошло не так</div>
    <div className="lead mt-1">Мы постараемся исправить это как можно скорее</div>
    <div className="mt-5 text-secondary" style={{ fontSize: "10rem" }}>500</div>
  </div>
}