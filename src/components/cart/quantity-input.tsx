'use client'

import { useEffect, useEffectEvent, useRef } from 'react'

import { buttonClass } from '@/components/ui/button'

import { useDebounceCallback } from '@/lib/debounce'

const MAX_QUANTITY = 10000
const DEBOUNCE_DELAY = 300

// The buttons and the field between them are joined, as in Bootstrap's small .input-group
const stepButtonClass = `${buttonClass({ variant: 'success', size: 'sm' })} relative w-[1.8rem] focus-visible:z-10`
const fieldClass = 'relative min-w-0 flex-1 rounded-none border-y px-2 py-1 text-sm leading-normal'

interface QuantityInputProps {
  quantity: number | undefined  // undefined when the product is not in the basket
  setQuantity: (quantity: number) => void
  packOnly: boolean
  packFactor: number
  isLoading?: boolean  // the basket is loading: a spinner shows in place of the field
  isPending?: boolean  // a change sent from here is on its way to the basket, until the basket is loaded again
}

// Products sold in packs only are counted in whole packs: the buttons step by the pack size
// and a typed quantity is rounded up to it. Zero removes the product from the basket.
// The field shows what was typed until the basket has it. A quantity entered while a change is on its way
// is held and sent after it: a second addition would add to the first one's quantity, and two updates
// could arrive in either order. The basket's quantity replaces the field only when nothing is waiting.
export default function QuantityInput({ quantity, setQuantity, packOnly, packFactor, isLoading = false, isPending = false }: QuantityInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const unsent = useRef(false)  // typed or stepped, still in the debounce
  const held = useRef<number | undefined>(undefined)  // entered while a change was on its way
  const step = packOnly && packFactor !== 1 ? packFactor : 1

  // The change is pending until the basket is loaded again, so quantity is up to date once it is done
  const settle = useEffectEvent(() => {
    if (isLoading || isPending || unsent.current)
      return
    if (held.current !== undefined) {
      const value = held.current
      held.current = undefined
      setQuantity(value)
    } else if (inputRef.current) {
      inputRef.current.value = String(quantity ?? 0)  // also after a change that failed
    }
  })

  useEffect(() => {
    settle()
  }, [quantity, isLoading, isPending])

  const updateQuantity = useDebounceCallback((value: number) => {
    unsent.current = false
    if (inputRef.current)
      inputRef.current.value = String(value)
    if (isPending) {
      held.current = value
    } else {
      held.current = undefined
      setQuantity(value)
    }
  }, DEBOUNCE_DELAY)

  const handleValueChange = (value: number) => {
    let v = value
    if (isNaN(v))
      v = quantity ?? 0
    else if (v < 0)
      v = 0
    else if (v > MAX_QUANTITY)
      v = MAX_QUANTITY
    if (step !== 1)
      v = Math.floor(packFactor * Math.ceil(v / packFactor))
    updateQuantity(v)
  }

  const handleInputChange = useDebounceCallback((value: string) => handleValueChange(+value), DEBOUNCE_DELAY)

  const modifyValue = (diff: number) => {
    if (!inputRef.current)
      return
    const v = (+inputRef.current.value || 0) + diff * step
    inputRef.current.value = String(v)
    unsent.current = true
    handleValueChange(v)
  }

  return (
    <div className="inline-flex w-28 items-stretch">
      <button
        className={`${stepButtonClass} rounded-e-none`}
        type="button"
        onClick={() => modifyValue(-1)}
        disabled={isLoading || isPending}>-</button>
      <input
        ref={inputRef}
        type="text"
        className={`${fieldClass} bg-white text-center text-body focus:z-10 focus:border-primary/50 focus:outline-none focus:ring-4 focus:ring-primary/25${isLoading ? " hidden" : ""}`}
        defaultValue={quantity ?? 0}
        onChange={(e) => {
          unsent.current = true
          handleInputChange(e.currentTarget.value)
        }} />
      <button className={`${fieldClass} flex items-center justify-center border-success text-success opacity-65${isLoading ? "" : " hidden"}`} type="button" disabled>
        <span className="inline-block size-4 animate-grow rounded-full bg-current opacity-0" role="status" aria-hidden="true"></span>
      </button>
      <button
        className={`${stepButtonClass} rounded-s-none`}
        type="button"
        onClick={() => modifyValue(1)}
        disabled={isLoading || isPending}>+</button>
    </div>
  )
}
