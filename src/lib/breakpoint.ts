import { useState, useEffect } from 'react'

const breakpoints = {
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
}

export const useBreakpoint = () => {
    const [breakpoint, setBreakpoint] = useState('xs')

    useEffect(() => {
        const handleResize = () => {
            const width = window.innerWidth
            if (width >= breakpoints.xl)
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
