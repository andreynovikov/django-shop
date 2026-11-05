import { AnonymousUser, User, UserBonus, UserCheck, UserEdit, UserForm } from '../types'
import { apiFetch, FormDataJson } from './fetch'

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

export async function updateUser(id: number, body: UserEdit) {
  return await apiFetch<User, UserEdit>(`users/${id}/`, {
    body,
    method: 'PUT',
  })
}

export async function registerUser(formData: FormData) {
  const body = Object.fromEntries(formData)
  return await apiFetch<User, FormDataJson>('users/', { body })
}

export async function loginUser(credentials: LoginCredentials) {
  return await apiFetch<LoginResult, LoginCredentials>('users/login/', {
    body: credentials
  })
}

export async function logoutUser() {
  return await apiFetch<void>('users/logout/')
}