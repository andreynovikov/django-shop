'use client'

import { Dispatch, SetStateAction, useEffect } from 'react'

import Image from 'next/image'
import { IconX } from '@tabler/icons-react'

interface ImageGalleryProps {
  currentImage: number,
  images: string[],
  open: boolean,
  setOpen: Dispatch<SetStateAction<boolean>>
}

export default function ImageGallery({ currentImage, images, open, setOpen }: ImageGalleryProps) {
  useEffect(() => {
    if (!open)
      return
    if (currentImage >= 0) {
      const el = document.getElementById(`gallery-image-${currentImage}`)
      if (el !== null)
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [currentImage, images, open])

  if (!open)
    return null

  return (
    <div className="sw-no-body-scroll fixed top-0 left-0 z-9998 h-screen w-screen bg-gray-100">
      <button
        className="absolute top-0 right-0 z-9999 p-4 text-dark"
        type="button"
        onClick={() => setOpen(false)}
        aria-label="Закрыть">
        <IconX size={16} stroke={2} />
      </button>
      <div className="size-full overflow-auto p-2 lg:p-6">
        <div className="grid gap-2 lg:grid-cols-2 lg:gap-4">
          {images.map((image, index) => (
            <div key={image} id={`gallery-image-${index}`}>
              <div className="relative mx-0 aspect-4/3 w-full bg-white lg:mx-1">
                <Image
                  src={image}
                  alt=""
                  fill
                  style={{ objectFit: 'contain' }}
                  sizes="(min-width: 1024px) 50vw, 100vw"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
