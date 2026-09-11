import { User, UserBonus, UserCheck, UserEdit, UserForm } from '../types'
import { apiFetch } from './fetch'

export const userKeys = {
  all: ['users'],
  form: () => [...userKeys.all, 'form'],
  details: () => [...userKeys.all, 'detail'],
  detail: (id: number) => [...userKeys.details(), id],
  current: () => [...userKeys.details(), 'current'],
  bonus: () => [...userKeys.details(), 'bonus'],
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
  return await apiFetch<User>('users/current/')
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