import { ChangeEvent } from 'react'

import Countdown from '@/components/countdown'
import { feedbackClass, formTextClass, inputClass } from '@/components/ui/form'

interface PhoneCodeInputProps {
  id: string
  delay: number // seconds until a new code can be requested, -1 while one is being requested
  attemptsLeft: number
  error?: string
  className?: string
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
  onResend: () => void
}

// The code from SMS that proves a new phone: at registration and when the phone is changed in the profile
export default function PhoneCodeInput({ id, delay, attemptsLeft, error, className = '', onChange, onResend }: PhoneCodeInputProps) {
  return (
    <>
      <input
        type="text"
        name="code"
        className={`${inputClass({ invalid: !!error })} ${className}`}
        id={id}
        placeholder="Код из смс"
        onChange={onChange}
        autoComplete="one-time-code"
        inputMode="numeric"
        maxLength={6}
        required
        autoFocus />
      {error && <div className={feedbackClass}>{error}</div>}
      <div className={formTextClass}>
        {/* when attempts run out, a new code can be requested at once */}
        <Countdown delay={attemptsLeft > 0 ? delay : 0} permanentPassword={false} reset={onResend} />
      </div>
    </>
  )
}
