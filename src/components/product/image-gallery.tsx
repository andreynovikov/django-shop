'use client'

import { createContext, ReactNode, useContext, useState } from 'react'

import Lightbox, { SlideImage } from 'yet-another-react-lightbox'

import { IconChevronCompactLeft, IconChevronCompactRight, IconX } from '@tabler/icons-react'

const GalleryContext = createContext<(index: number) => void>(() => {})

// Full screen lightbox over the product page, opened from the images of the server rendered page
export function ProductImageGallery({ slides, children }: { slides: SlideImage[], children: ReactNode }) {
  const [currentIndex, setCurrentIndex] = useState(-1)

  return (
    <GalleryContext.Provider value={setCurrentIndex}>
      {children}
      <Lightbox
        open={currentIndex !== -1}
        close={() => setCurrentIndex(-1)}
        index={currentIndex}
        on={{ view: ({ index }) => setCurrentIndex(index) }}
        slides={slides}
        carousel={{
          finite: true
        }}
        render={{
          iconPrev: () => <IconChevronCompactLeft size={64} />,
          iconNext: () => <IconChevronCompactRight size={64} />,
          iconClose: () => <IconX size={64} />
        }}
      />
    </GalleryContext.Provider>
  )
}

// Opens the lightbox at the slide
export function GalleryLink({ index, className, children }: { index: number, className?: string, children: ReactNode }) {
  const open = useContext(GalleryContext)

  return (
    <a onClick={() => open(index)} className={className} style={{ cursor: "pointer" }}>
      {children}
    </a>
  )
}
