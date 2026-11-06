'use client'

import { useEffect, useRef } from 'react'

import { useDebounceCallback } from '@/lib/debounce'

const MAX_QUANTITY = 10000
const DEBOUNCE_DELAY = 300

interface QuantityInputProps {
  quantity: number | undefined  // undefined until the basket is loaded
  setQuantity: (quantity: number) => void
  packOnly: boolean
  packFactor: number
  isLoading?: boolean
}

// Products sold in packs only are counted in whole packs: the buttons step by the pack size
// and a typed quantity is rounded up to it. Zero removes the product from the basket.
export default function QuantityInput({ quantity, setQuantity, packOnly, packFactor, isLoading = false }: QuantityInputProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const step = packOnly && packFactor !== 1 ? packFactor : 1

  useEffect(() => {
    if (quantity !== undefined && inputRef.current)
      inputRef.current.value = String(quantity)
  }, [quantity])

  const updateQuantity = useDebounceCallback((value: number) => {
    setQuantity(value)
    if (inputRef.current)
      inputRef.current.value = String(value)
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
    handleValueChange(v)
  }

  return (
    <div className="input-group input-group-sm d-inline-flex" style={{ width: '7rem' }}>
      <button
        className="btn btn-success"
        type="button"
        style={{ width: '1.8rem' }}
        onClick={() => modifyValue(-1)}
        disabled={isLoading}>-</button>
      <input
        ref={inputRef}
        type="text"
        className={"form-control text-center" + (isLoading ? " d-none" : "")}
        defaultValue={quantity ?? 0}
        onChange={(e) => handleInputChange(e.currentTarget.value)} />
      <button className={"form-control btn btn-outline-success" + (isLoading ? "" : " d-none")} type="button" disabled>
        <span className="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span>
      </button>
      <button
        className="btn btn-success"
        type="button"
        style={{ width: '1.8rem' }}
        onClick={() => modifyValue(1)}
        disabled={isLoading}>+</button>
    </div>
  )
}
