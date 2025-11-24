'use client'

import { Dispatch, SetStateAction, useEffect } from 'react'

import Image from 'next/image'

interface ImageGalleryProps {
  currentImage: string,
  images: string[],
  open: boolean,
  setOpen: Dispatch<SetStateAction<boolean>>
}

export default function ImageGallery({ currentImage, images, open, setOpen }: ImageGalleryProps) {
  useEffect(() => {
    if (!open)
      return
    const index = images.indexOf(currentImage)
    if (index >= 0) {
      const el = document.getElementById(`gallery-image-${index}`)
      if (el !== null)
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [currentImage, images, open])

  if (!open)
    return null

  return (
    <div className="position-fixed start-0 top-0 vw-100 vh-100 bg-secondary sw-no-body-scroll" style={{ zIndex: 9998 }}>
      <button
        className="btn btn-link position-absolute top-0 end-0 p-3 text-dark"
        style={{ zIndex: 9999 }}
        type="button"
        onClick={() => setOpen(false)}>
        <i className="ci-close" />
      </button>
      <div className="container-fluid w-100 h-100 p-2 p-lg-4 overflow-auto">
        <div className="row g-2 g-lg-3">
          {images.map((image, index) => (
            <div key={image} id={`gallery-image-${index}`} className="col-12 col-lg-6">
              <div className="position-relative mx-0 mx-lg-1 bg-white" style={{ width: "100%", aspectRatio: "4/3" }}>
                <Image
                  src={image}
                  alt=""
                  fill
                  style={{ objectFit: 'contain' }}
                  sizes="(min-width: 992px) 50vw, 100vw"
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}