import { AnonymousUser, PhoneCodeSent, User, UserBonus, UserCheck, UserEdit, UserForm } from '../types'
import { apiFetch } from './fetch'

export const userKeys = {
  all: ['users'],
  form: () => [...userKeys.all, 'form'],
  details: () => [...userKeys.all, 'detail'],
  detail: (id: number) => [...userKeys.details(), id],
  current: () => [...userKeys.details(), 'current'],
  bonus: () => [...userKeys.details(), 'bonus'],
}

export interface LoginResult {
  id: number
  registered: boolean
}

// Registration form fields, and with the code from SMS: code and an optional permanent password
export type RegistrationData = Record<string, string>

export interface LoginCredentials {
  phone: string
  password?: string
  permanent_password?: string
  ctx?: string
}

export function normalizePhone(phone: string) {
  phone = phone.replaceAll(/[^0-9\+]/g, '')
  if (!phone.startsWith('+')) {
    if (phone.startsWith('7') && phone.length === 11)
      phone = '+' + phone
    else
      phone = '+7' + phone
  }
  return phone
}

export async function checkUser(phone: string, reset: boolean) {
  return await apiFetch<UserCheck>('users/' + normalizePhone(phone) + '/check/', {
    body: { reset }
  })
}

export async function currentUser() {
  return await apiFetch<AnonymousUser | User>('users/current/')
}

export async function getUserForm() {
  return await apiFetch<UserForm>('users/form/')
}

export async function getUserBonus() {
  return await apiFetch<UserBonus>('users/bonus/')
}

export async function loadUser(id: number) {
  return await apiFetch<User>(`users/${id}/`)
}

export function isPhoneCodeSent(result: User | PhoneCodeSent): result is PhoneCodeSent {
  return !('id' in result)
}

// A new phone is saved only with the code sent to it: without one, nothing is saved and a code is sent
export async function updateUser(id: number, body: UserEdit) {
  return await apiFetch<User | PhoneCodeSent, UserEdit>(`users/${id}/`, {
    body,
    method: 'PUT',
  })
}

// Without the code it checks the data and sends one to the phone, with it it creates the account and logs in
export async function registerUser(body: RegistrationData) {
  return await apiFetch<User | PhoneCodeSent, RegistrationData>('users/', { body })
}

// Sends the link that confirms the user's email again
export async function sendEmailLink(id: number) {
  return await apiFetch<void>(`users/${id}/email-link/`, { method: 'POST' })
}

// The token from the link, it needs no session: the link may be opened on another device
export async function confirmEmail(token: string) {
  return await apiFetch<{ email: string }, { token: string }>('users/confirm-email/', {
    body: { token }
  })
}

export async function loginUser(credentials: LoginCredentials) {
  return await apiFetch<LoginResult, LoginCredentials>('users/login/', {
    body: credentials
  })
}

export async function logoutUser() {
  return await apiFetch<void>('users/logout/', { method: 'POST' })
}