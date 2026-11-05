'use client'

import { useEffect, useState } from 'react'

import LoginForm from '@/components/user/login-form'

// Registration passes the new phone to the login page here rather than in the URL,
// where Metrika would see it and a link could make the page send an SMS or create an account
const registeredPhoneKey = 'registeredPhone'

export function passPhoneToLogin(phone: string) {
  sessionStorage.setItem(registeredPhoneKey, phone)
}

export default function LoginPageForm() {
  const [phone, setPhone] = useState<string>()

  useEffect(() => {
    const registeredPhone = sessionStorage.getItem(registeredPhoneKey)
    if (registeredPhone === null)
      return
    // Taken once, so a reload or a later visit starts with an empty form, as any login does
    sessionStorage.removeItem(registeredPhoneKey)
    // sessionStorage is read only after hydration, the server can't see it
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setPhone(registeredPhone)
  }, [])

  return <LoginForm key={phone} ctx={phone ? 'reg' : 'login'} phone={phone} />
}
