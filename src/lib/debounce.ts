import { useState, useEffect, useRef, useCallback } from 'react'

// Reusable hook for debouncing a value
export function useDebounce<T>(value: T, delay: number) {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    // Set a timer to update the debounced value after the specified delay
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    // If the value changes before the delay finishes, clear the previous timer
    return () => {
      clearTimeout(timer)
    };
  }, [value, delay])

  return debouncedValue
}

type AnyFunction = (...args: any[]) => void

// Reusable hook for debouncing an action
export function useDebounceCallback<T extends AnyFunction>(
  callback: T, 
  delay: number
): (...args: Parameters<T>) => void {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const callbackRef = useRef<T>(callback)

  // Keep track of the latest callback to avoid stale closures
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  // Clean up the timeout when the component unmounts
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // Return a stable debounced function using the parameters type of T
  return useCallback((...args: Parameters<T>): void => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      callbackRef.current(...args)
    }, delay)
  }, [delay])
}