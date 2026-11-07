import { useState, useEffect } from 'react'

// Tailwind's breakpoints, xxl is its 2xl
const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  xxl: 1536,
}

export const useBreakpoint = () => {
  const [breakpoint, setBreakpoint] = useState('xs')

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth
      if (width >= breakpoints.xxl)
        setBreakpoint('xxl')
      else if (width >= breakpoints.xl)
        setBreakpoint('xl')
      else if (width >= breakpoints.lg)
        setBreakpoint('lg')
      else if (width >= breakpoints.md)
        setBreakpoint('md')
      else if (width >= breakpoints.sm)
        setBreakpoint('sm')
      else
        setBreakpoint('xs')
    }

    handleResize() // Initial check
    window.addEventListener('resize', handleResize)

    return () => window.removeEventListener('resize', handleResize)
  }, []);

  return breakpoint
}
