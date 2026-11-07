// Tailwind classes of Cartzilla's round carousel arrows. Swiper finds them by the nav-button-prev/next classes and adds
// swiper-button-disabled at the ends, where they fade out.

const sizes = {
  sm: 'size-9 -mt-[1.125rem]',
  md: 'size-11 -mt-[1.375rem]',
  lg: 'size-13 -mt-[1.625rem]',
}

// Sizes of the arrow icons in them
export const carouselIconSizes = { sm: 11, md: 13, lg: 15 }

export function carouselNavClass({ side, size = 'md', fromSm = false }: { side: 'prev' | 'next', size?: keyof typeof sizes, fromSm?: boolean }) {
  return `nav-button-${side} ${side === 'prev' ? 'left-0' : 'right-0'} ${fromSm ? 'hidden sm:flex' : 'flex'} ${sizes[size]} absolute top-1/2 z-10 cursor-pointer items-center justify-center rounded-full border border-gray-300 bg-white text-body transition-all duration-300 [&.swiper-button-disabled]:opacity-0!`
}
