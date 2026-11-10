import { APIRequestContext, Page, Route } from '@playwright/test'

import type { AnonymousUser, Basket, BasketItem, BasketItemProduct, Order, OrderInfo, OrderItem, PaginatedResult, ProductInfo, User } from '@/lib/types'
import {
  DELIVERY_UNKNOWN,
  PAYMENT_CARD,
  PAYMENT_CREDIT,
  PAYMENT_TRANSFER,
  PAYMENT_UNKNOWN,
  STATUS_CANCELED,
  STATUS_COLLECTED,
  STATUS_DONE,
  STATUS_FINISHED,
  STATUS_NEW,
} from '@/components/order/status-badge'

import { checkContract } from './contract'

// Messages and status codes follow django-shop: sewingworld/api.py and sewingworld/serializers.py
const NOT_AUTHENTICATED = 'Учетные данные не были предоставлены.'
const PERMISSION_DENIED = 'У вас недостаточно прав для выполнения данного действия.'
const NOT_FOUND = 'Не найдено.'
const THROTTLED = 'Запрос был проигнорирован.'
const PHONE_TAKEN = 'Пользователь с указанным номером уже зарегестрирован'
const EMAIL_TAKEN = 'Пользователь с указанным адресом уже зарегестрирован'
const USERNAME_TAKEN = 'Пользователь с указанным псевдонимом уже зарегестрирован'
const INVALID_PHONE = 'Укажите мобильный номер в формате +7 (999) 111-22-33'
const WRONG_CODE = 'Неверный или устаревший код'
const PASSWORD_TOO_SHORT = 'Введённый пароль слишком короткий. Он должен состоять из как минимум 8 символов.'
const NOTHING_TO_CONFIRM = 'Адрес не указан или уже подтверждён'
const BAD_EMAIL_LINK = 'Ссылка недействительна или устарела'
const BAD_BASKET_LINK = 'Ссылка недействительна'
const TOO_MANY_PASSWORDS = 'Слишком много попыток входа с неверным паролем. Войдите с кодом из смс.'

const STATUS_TEXTS: Record<number, string> = {
  [STATUS_NEW]: 'новый заказ',
  [STATUS_COLLECTED]: 'собран',
  [STATUS_DONE]: 'завершён',
}

const PAYMENT_TEXTS: Record<number, string> = {
  [PAYMENT_UNKNOWN]: 'уточняется',
  [PAYMENT_CARD]: 'банковская карта',
}

const PAGE_SIZE = 20
const CODE_MAX_ATTEMPTS = 5
const CODE_RESEND_DELAY = 240
const CODES_PER_PHONE = 5 // check_phone throttle, smsLog holds what it counts, login and phone codes alike
const EMAIL_LINKS_PER_USER = 3 // email_link throttle
const PASSWORD_MIN_LENGTH = 8 // AUTH_PASSWORD_VALIDATORS
const PASSWORD_FAILURES_PER_PHONE = 10 // login_phone throttle, wrong permanent passwords only

interface LoginCode {
  code: string
  attempts: number
  issued: number // a timestamp
}

export interface FakeUser extends User {
  password?: string // the permanent password
  loginCode?: LoginCode // the last SMS code, until it is used up
}

export interface LoggedRequest {
  method: string
  path: string // relative to /api/v0/, e.g. "users/+79161234567/check/"
  body: unknown
}

type FakeOrder = Order & { user: number }

type Body = Record<string, unknown>

interface FakeResponse {
  status: number
  body?: unknown
}

const ok = (body: unknown): FakeResponse => ({ status: 200, body })
const noContent = (): FakeResponse => ({ status: 204 })
const notAuthenticated = (): FakeResponse => ({ status: 403, body: { detail: NOT_AUTHENTICATED } })
const notFound = (): FakeResponse => ({ status: 404, body: { detail: NOT_FOUND } })
const throttled = (): FakeResponse => ({ status: 429, body: { detail: THROTTLED } })

const retryAfter = ({ issued }: LoginCode) => Math.max(0, Math.ceil((issued - Date.now()) / 1000) + CODE_RESEND_DELAY)

const newCode = () => String(100000 + Math.floor(Math.random() * 900000))

// PhoneValidator: +7 and ten digits
const phoneErrors = (phone: string): Record<string, string[]> => /^\+7\d{10}$/.test(phone) ? {} : { phone: [INVALID_PHONE] }

const passwordErrors = (field: string, password: string): Record<string, string[]> =>
  password.length > 0 && password.length < PASSWORD_MIN_LENGTH ? { [field]: [PASSWORD_TOO_SHORT] } : {}

export function normalizePhone(phone: string) {
  const digits = phone.replaceAll(/\D/g, '')
  if (phone.trim().startsWith('+') && !digits.startsWith('7'))
    return '+' + digits // another country, as ShopUserManager.normalize_phone keeps it
  return '+7' + (digits.length === 11 ? digits.slice(1) : digits)
}

// The backend serializes basket products with NonNullModelSerializer, which leaves out empty values
function toBasketProduct(product: ProductInfo | BasketItemProduct): BasketItemProduct {
  const optional = { whatis: product.whatis, partnumber: product.partnumber, article: product.article, image: product.image }
  return {
    id: product.id,
    code: product.code,
    title: product.title,
    ...Object.fromEntries(Object.entries(optional).filter(([, value]) => value)),
    ws_pack_only: product.ws_pack_only ?? false,
    pack_factor: product.pack_factor ?? 1,
    price: product.price,
    cost: product.cost,
    instock: Math.max(Math.min(product.instock, 10), 0),
  }
}

// The product discount is the only discount the fake applies
function itemPrices(product: BasketItemProduct, quantity: number) {
  const discount = product.price - product.cost
  return {
    discount,
    discount_text: discount > 0 ? `${Math.round(discount * 100 / product.price)}%` : '',
    cost: product.cost,
    price: product.cost * quantity,
  }
}

/*
In-memory stand-in for the user part of the backend: session, basket, favorites and orders.
Requests it does not handle fall through, so GET requests still read the production backend
(catalog, products, stores), and other methods are blocked by the blockApiWrites fixture.
*/
export class FakeBackend {
  readonly requests: LoggedRequest[] = []
  readonly smsLog: { phone: string, code: string }[] = []
  // confirmation links sent by email, see lastEmailLink()
  readonly emailLog: { user: number, email: string, token: string }[] = []
  // requests and answers that differ from the API schema, see contract.ts
  readonly violations: string[] = []

  private users: FakeUser[] = []
  private sessionUserId: number | null = null
  private basket: { id: number, items: { id: number, product: BasketItemProduct, quantity: number }[], utm_source: string } | null = null
  private favorites = new Map<number, number[]>()
  private orders: FakeOrder[] = []
  private products = new Map<number, BasketItemProduct>()
  private nextId = { user: 1, basket: 1, item: 1, order: 100001 }
  // codes that prove a new phone, by phone and the user moving to it ('' when registering), see PhoneCode
  private phoneCodes = new Map<string, LoginCode>()
  // wrong permanent passwords by phone, see LoginSerializer.check_password
  private passwordFailures = new Map<string, number>()
  // baskets of other sessions that a link in the abandoned basket email can clear, by the signed id
  private signedBaskets = new Map<string, number>()

  constructor(private request: APIRequestContext) { }

  async install(page: Page) {
    await page.route('**/api/v0/**', route => this.handle(route))
  }

  get user() {
    return this.users.find(user => user.id === this.sessionUserId)
  }

  findUser(phone: string) {
    const normalized = normalizePhone(phone)
    return this.users.find(user => user.phone === normalized)
  }

  addUser(user: Partial<FakeUser> = {}): FakeUser {
    const id = user.id ?? this.nextId.user++
    const name = user.name ?? 'Тестовый покупатель'
    const created: FakeUser = {
      id,
      phone: '+79161234567',
      name,
      full_name: name,
      gravatar: '',
      username: `user${id}`,
      email: '',
      postcode: '',
      city: '',
      address: '',
      discount: 0,
      bonuses: 0,
      expiring_bonuses: 0,
      expiration_date: null,
      permanent_password: false,
      last_login: new Date().toISOString(),
      date_joined: new Date().toISOString(),
      email_verified: Boolean(user.email), // as the migration left existing users
      phone_verified: true,
      ...user,
    }
    created.phone = normalizePhone(created.phone)
    this.users.push(created)
    return created
  }

  // Seeds a user and starts their session without going through the login form
  signIn(user: Partial<FakeUser> = {}) {
    const created = this.addUser(user)
    this.sessionUserId = created.id
    return created
  }

  addProducts(...products: (ProductInfo | BasketItemProduct)[]) {
    for (const product of products)
      this.products.set(product.id, toBasketProduct(product))
  }

  // Seeds an order of the given user, the signed in one by default
  addOrder(order: Partial<Omit<Order, 'items'>> & { items?: { product: ProductInfo | BasketItemProduct, quantity?: number }[] } = {}, user = this.user) {
    if (user === undefined)
      throw new Error('addOrder needs a user')
    const { items = [], ...fields } = order
    const status = fields.status ?? STATUS_NEW
    const payment = fields.payment ?? PAYMENT_UNKNOWN
    const created: FakeOrder = {
      id: this.nextId.order++,
      created: new Date().toISOString(),
      status,
      status_text: STATUS_TEXTS[status] ?? '',
      payment,
      payment_text: PAYMENT_TEXTS[payment] ?? '',
      paid: false,
      total: 0,
      delivery: DELIVERY_UNKNOWN,
      delivery_price: 0,
      delivery_tracking_number: '',
      delivery_info: '',
      delivery_dispatch_date: null,
      delivery_handing_date: null,
      delivery_time_from: null,
      delivery_time_till: null,
      store: null,
      name: user.name,
      phone: user.phone,
      email: user.email,
      address: user.address,
      is_firm: false,
      firm_name: '',
      firm_address: '',
      firm_details: '',
      comment: '',
      ...fields,
      items: items.map(({ product, quantity = 1 }) => this.orderItem(toBasketProduct(product), quantity)),
      user: user.id,
    }
    if (fields.total === undefined)
      created.total = created.items.reduce((total, item) => total + item.price, 0) + created.delivery_price
    this.orders.push(created)
    return this.orderJson(created)
  }

  // Seeds favorites of the given user, the signed in one by default
  addFavorites(products: { id: number }[], user = this.user) {
    if (user === undefined)
      throw new Error('addFavorites needs a user')
    this.favorites.set(user.id, [...this.favorites.get(user.id) ?? [], ...products.map(({ id }) => id)])
  }

  // Seeds the basket of the session
  addBasket(...items: { product: ProductInfo | BasketItemProduct, quantity?: number }[]) {
    this.basket = {
      id: this.nextId.basket++,
      items: items.map(({ product, quantity = 1 }) => ({ id: this.nextId.item++, product: toBasketProduct(product), quantity })),
      utm_source: '',
    }
    return this.basket.id
  }

  // The signed id in the link that clears the basket, as the abandoned basket email has it
  basketClearSign(id: number) {
    const sign = `${id}:signature`
    this.signedBaskets.set(sign, id)
    return sign
  }

  get basketUtmSource() {
    return this.basket?.utm_source
  }

  get basketItems() {
    return this.basket?.items.map(({ product, quantity }) => ({ product: product.id, quantity })) ?? []
  }

  get favoriteIds() {
    return this.sessionUserId === null ? [] : this.favorites.get(this.sessionUserId) ?? []
  }

  lastOrder() {
    return this.orders.at(-1)
  }

  // As if the code was sent that many seconds earlier
  ageLoginCode(phone: string, seconds: number) {
    this.findUser(phone)!.loginCode!.issued -= seconds * 1000
  }

  lastSmsCode(phone: string) {
    const normalized = normalizePhone(phone)
    return this.smsLog.findLast(sms => sms.phone === normalized)?.code
  }

  // The storefront page that the last confirmation link sent to the address opens
  lastEmailLink(email: string) {
    const token = this.emailLog.findLast(link => link.email === email)?.token
    return token === undefined ? undefined : `/confirm-email/?token=${token}`
  }

  requestsTo(method: string, path: string | RegExp) {
    return this.requests.filter(request => request.method === method &&
      (typeof path === 'string' ? request.path === path : path.test(request.path)))
  }

  private async handle(route: Route) {
    const request = route.request()
    const url = new URL(request.url())
    const path = url.pathname.replace(/^\/api\/v0\//, '')
    const segments = path.split('/').filter(Boolean).map(decodeURIComponent)
    let body: unknown = null
    try {
      body = request.postDataJSON()
    } catch {
      body = request.postData()
    }
    this.requests.push({ method: request.method(), path: decodeURIComponent(path), body })

    const response = await this.respond(request.method(), segments, url.searchParams, (body ?? {}) as Body)
    if (response === undefined)
      return route.fallback()
    const query = Object.fromEntries([...new Set(url.searchParams.keys())].map(key => {
      const values = url.searchParams.getAll(key)
      return [key, values.length === 1 ? values[0] : values]
    }))
    this.violations.push(...await checkContract({
      method: request.method(),
      path: decodeURIComponent(url.pathname),
      query,
      headers: request.headers(),
      body: body ?? undefined,
    }, response))
    if (response.status === 204)
      return route.fulfill({ status: 204 })
    return route.fulfill({ status: response.status, json: response.body })
  }

  private async respond(method: string, segments: string[], query: URLSearchParams, body: Body) {
    const [resource, ...rest] = segments
    switch (resource) {
      case 'users':
        return this.respondUsers(method, rest, body)
      case 'baskets':
        return this.respondBaskets(method, rest, body)
      case 'orders':
        return this.respondOrders(method, rest, query, body)
      case 'favorites':
        return this.respondFavorites(method, rest, body)
      case 'serials':
        return this.respondSerials(method, rest, body)
    }
    return undefined
  }

  private respondUsers(method: string, [key, action]: string[], body: Body) {
    if (method === 'GET' && key === 'current')
      return ok(this.user ? this.userJson(this.user) : { id: null, is_anonymous: true } as AnonymousUser)
    if (method === 'POST' && key === 'logout') {
      // the backend keeps the basket of the session
      this.sessionUserId = null
      return noContent()
    }
    if (method === 'POST' && key === undefined)
      return this.register(body)
    if (method === 'POST' && key === 'login')
      return this.login(body)
    if (method === 'POST' && action === 'check')
      return this.check(key, body)
    if (method === 'POST' && key === 'confirm-email')
      return this.confirmEmail(body)
    if (/^\d+$/.test(key ?? '') && (action === undefined || action === 'email-link')) {
      if (this.user?.id !== +key)
        return { status: 403, body: { detail: PERMISSION_DENIED } }
      if (method === 'GET' && action === undefined)
        return ok(this.userJson(this.user))
      if (method === 'PUT' && action === undefined)
        return this.updateUser(this.user, body)
      if (method === 'POST' && action === 'email-link') {
        if (!this.user.email || this.user.email_verified)
          return { status: 400, body: { email: [NOTHING_TO_CONFIRM] } }
        return this.sendEmailLink(this.user) ? noContent() : throttled()
      }
    }
    // users/form/ and the like are the same for everybody, so they come from the backend
    return undefined
  }

  // Follows UserViewSet.create: the data, then the same data with the code sent to the phone
  private register(body: Body) {
    const phone = normalizePhone(String(body.phone ?? ''))
    const email = String(body.email ?? '')
    const username = String(body.username ?? '')
    const password = String(body.password ?? '')
    // a taken address is told only with the code, which is kept for the corrected one
    const { email: emailTaken, ...errors } = {
      ...this.uniqueErrors(undefined, phone, email, username),
      ...phoneErrors(phone),
      ...passwordErrors('password', password),
    }
    if (Object.keys(errors).length > 0)
      return { status: 400, body: errors }
    if (!body.code)
      return this.sendPhoneCode(phone)
    if (emailTaken !== undefined) {
      if (!this.verifyPhoneCode(phone, undefined, String(body.code), true))
        return { status: 400, body: { code: [WRONG_CODE] } }
      return { status: 400, body: { email: emailTaken } }
    }
    if (!this.verifyPhoneCode(phone, undefined, String(body.code)))
      return { status: 400, body: { code: [WRONG_CODE] } }
    const user = this.addUser({
      phone, email, username, name: String(body.name ?? ''),
      email_verified: false, phone_verified: true,
      permanent_password: password.length > 0, password: password || undefined,
    })
    this.sessionUserId = user.id
    if (email)
      this.sendEmailLink(user)
    return { status: 201, body: this.userJson(user) }
  }

  // Follows send_phone_code_once: a code sent recently is kept, and codes count against the phone's limit
  private sendPhoneCode(phone: string, user?: FakeUser) {
    const key = `${phone}:${user?.id ?? ''}`
    let phoneCode = this.phoneCodes.get(key)
    if (phoneCode === undefined || retryAfter(phoneCode) === 0) {
      if (this.smsLog.filter(sms => sms.phone === phone).length >= CODES_PER_PHONE)
        return throttled()
      const code = newCode()
      phoneCode = { code, attempts: 0, issued: Date.now() }
      this.phoneCodes.set(key, phoneCode)
      this.smsLog.push({ phone, code })
    }
    return { status: 202, body: { phone, retry_after: retryAfter(phoneCode), attempts_left: CODE_MAX_ATTEMPTS - phoneCode.attempts } }
  }

  // A kept code has the attempt counted all the same
  private verifyPhoneCode(phone: string, user: FakeUser | undefined, code: string, keep = false) {
    const key = `${phone}:${user?.id ?? ''}`
    const phoneCode = this.phoneCodes.get(key)
    if (phoneCode === undefined)
      return false
    phoneCode.attempts++
    if ((code === phoneCode.code && !keep) || phoneCode.attempts >= CODE_MAX_ATTEMPTS)
      this.phoneCodes.delete(key)
    return code === phoneCode.code
  }

  // Follows queue_email_confirmation, the link is in emailLog instead
  private sendEmailLink(user: FakeUser) {
    if (this.emailLog.filter(link => link.user === user.id).length >= EMAIL_LINKS_PER_USER)
      return false
    this.emailLog.push({ user: user.id, email: user.email, token: `${user.id}-${Math.random().toString(36).slice(2)}` })
    return true
  }

  private confirmEmail(body: Body) {
    const link = this.emailLog.find(link => link.token === body.token)
    const user = this.users.find(user => user.id === link?.user && user.email === link.email)
    if (user === undefined)
      return { status: 400, body: { token: [BAD_EMAIL_LINK] } }
    user.email_verified = true
    return ok({ email: user.email })
  }

  // Starts an SMS login, the code is in smsLog instead. Follows UserViewSet.check
  private check(phone: string, body: Body) {
    if (Object.keys(phoneErrors(normalizePhone(phone))).length > 0)
      return { status: 400, body: phoneErrors(normalizePhone(phone)) }
    const user = this.findUser(phone)
    if (user === undefined)
      return notFound()
    const permanent = user.permanent_password
    const reset = Boolean(body.reset)
    let loginCode: LoginCode | undefined
    if (!permanent || reset) {
      loginCode = user.loginCode
      if (loginCode === undefined || retryAfter(loginCode) === 0) {
        if (this.smsLog.filter(sms => sms.phone === user.phone).length >= CODES_PER_PHONE)
          return throttled()
        const code = newCode()
        loginCode = user.loginCode = { code, attempts: 0, issued: Date.now() }
        this.smsLog.push({ phone: user.phone, code })
      }
    }
    return ok({
      phone: user.phone,
      permanent_password: permanent && !reset,
      retry_after: loginCode ? retryAfter(loginCode) : 0,
      attempts_left: loginCode ? CODE_MAX_ATTEMPTS - loginCode.attempts : 0,
    })
  }

  private login(body: Body) {
    const phone = normalizePhone(String(body.phone ?? ''))
    // field errors come first, so a code sent with a short password is not used up
    const tooShort = passwordErrors('permanent_password', String(body.permanent_password ?? ''))
    if (Object.keys(tooShort).length > 0)
      return { status: 400, body: tooShort }
    if (Object.keys(phoneErrors(phone)).length > 0)
      return notAuthenticated()
    let user = this.findUser(phone)
    if (user === undefined && ['order', 'preorder', 'warranty'].includes(String(body.ctx))) {
      // the backend silently registers a buyer, without sending a code or taking a permanent password
      user = this.addUser({ phone, name: '', username: '', phone_verified: false })
      this.sessionUserId = user.id
      return ok({ id: user.id, registered: true })
    }
    if (user === undefined || !body.password)
      return notAuthenticated()
    const checked = this.checkCredentials(user, String(body.password))
    if (checked === 'throttled')
      return { status: 429, body: { detail: TOO_MANY_PASSWORDS } }
    if (!checked)
      return notAuthenticated()
    if (typeof body.permanent_password === 'string' && body.permanent_password.length > 0) {
      user.password = body.permanent_password
      user.permanent_password = true
    }
    this.sessionUserId = user.id
    return ok({ id: user.id, registered: false })
  }

  // Follows LoginSerializer.check_credentials and LoginCode.verify, except that codes don't expire here.
  // Wrong permanent passwords are limited per phone, codes are not.
  private checkCredentials(user: FakeUser, password: string): boolean | 'throttled' {
    const loginCode = user.loginCode
    if (loginCode !== undefined) {
      loginCode.attempts++
      if (password === loginCode.code) {
        user.loginCode = undefined
        user.password = undefined
        user.permanent_password = false
        if (!user.phone_verified) {
          // proven for the first time: an address confirmed before may be a stranger's
          user.phone_verified = true
          user.email_verified = false
        }
        return true
      }
      if (loginCode.attempts >= CODE_MAX_ATTEMPTS)
        user.loginCode = undefined
    }
    if (!user.permanent_password)
      return false
    const failures = this.passwordFailures.get(user.phone) ?? 0
    if (failures >= PASSWORD_FAILURES_PER_PHONE)
      return 'throttled'
    if (password === user.password)
      return true
    this.passwordFailures.set(user.phone, failures + 1)
    return false
  }

  // Follows UserViewSet.update: a new phone is saved only with the code sent to it
  private updateUser(user: FakeUser, body: Body) {
    const phone = normalizePhone(String(body.phone ?? user.phone))
    const email = String(body.email ?? user.email)
    const username = String(body.username ?? user.username)
    const errors = { ...this.uniqueErrors(user, phone, email, username), ...phoneErrors(phone) }
    if (Object.keys(errors).length > 0)
      return { status: 400, body: errors }
    if (phone !== user.phone) {
      if (!body.code)
        return this.sendPhoneCode(phone, user)
      if (!this.verifyPhoneCode(phone, user, String(body.code)))
        return { status: 400, body: { code: [WRONG_CODE] } }
      user.phone_verified = true
    }
    const emailChanged = email !== user.email
    const name = String(body.name ?? user.name)
    Object.assign(user, { name, full_name: name, phone, email, username, address: String(body.address ?? user.address) })
    if (emailChanged) {
      user.email_verified = false
      if (email)
        this.sendEmailLink(user)
    }
    return ok(this.userJson(user))
  }

  private uniqueErrors(user: FakeUser | undefined, phone: string, email: string, username: string) {
    const others = this.users.filter(other => other !== user)
    const errors: Record<string, string[]> = {}
    if (others.some(other => other.phone === phone))
      errors.phone = [PHONE_TAKEN]
    if (email && others.some(other => other.email === email))
      errors.email = [EMAIL_TAKEN]
    if (username && others.some(other => other.username === username))
      errors.username = [USERNAME_TAKEN]
    return errors
  }

  private async respondBaskets(method: string, [id, action]: string[], body: Body) {
    if (method === 'GET' && id === undefined)
      return ok(this.basket ? [this.basketJson()] : [])
    if (method === 'POST' && id === undefined) {
      this.basket ??= { id: this.nextId.basket++, items: [], utm_source: '' }
      return { status: 201, body: this.basketJson() }
    }
    if (method === 'POST' && id === 'restore')
      return this.restoreBasket(body)
    if (method === 'POST' && id === 'clear') {
      // follows BasketViewSet.clear: whichever session has the basket
      const basketId = this.signedBaskets.get(String(body.sign ?? ''))
      if (basketId === undefined)
        return { status: 400, body: { sign: [BAD_BASKET_LINK] } }
      this.signedBaskets.delete(String(body.sign))
      if (this.basket?.id === basketId)
        this.basket = null
      return noContent()
    }
    if (method !== 'POST' || !['add', 'update', 'remove'].includes(action))
      return undefined
    const basket = this.basket
    if (basket === null || basket.id !== +id)
      return notFound()

    const product = await this.product(Number(body.product))
    if (product === undefined)
      return { status: 400, body: { product: [`Недопустимый первичный ключ "${body.product}" - объект не существует.`] } }
    const item = basket.items.find(item => item.product.id === product.id)
    const quantity = typeof body.quantity === 'number' ? body.quantity : undefined

    if (action === 'add') {
      if (item)
        item.quantity += quantity ?? 1
      else
        basket.items.push({ id: this.nextId.item++, product, quantity: quantity ?? 1 })
    } else if (action === 'update') {
      const updated = Math.max(quantity ?? item?.quantity ?? 1, 0)
      if (updated === 0)
        basket.items = basket.items.filter(other => other !== item)
      else if (item)
        item.quantity = updated
      else
        basket.items.push({ id: this.nextId.item++, product, quantity: updated })
    } else {
      basket.items = basket.items.filter(other => other !== item)
    }
    if (action !== 'add' && basket.items.length === 0)
      this.basket = null
    return noContent()
  }

  // Follows BasketViewSet.restore and Basket.parse_link_contents: a session that has a basket keeps it
  private async restoreBasket(body: Body) {
    if (this.basket !== null)
      return noContent()
    const items = []
    for (const part of String(body.contents ?? '').split(',')) {
      const match = /^(\d{1,9})\*(\d{1,5})$/.exec(part.trim())
      const quantity = Number(match?.[2])
      const product = match && quantity > 0 && quantity <= 32767 ? await this.product(Number(match[1])) : undefined
      if (product !== undefined)
        items.push({ id: this.nextId.item++, product, quantity })
    }
    if (items.length > 0)
      this.basket = { id: this.nextId.basket++, items, utm_source: String(body.utm_source ?? '').replaceAll(/\W/g, '_').slice(0, 20) }
    return noContent()
  }

  private respondOrders(method: string, [id, action]: string[], query: URLSearchParams, body: Body) {
    const user = this.user
    const orders = this.orders.filter(order => order.user === user?.id).toSorted((a, b) => b.id - a.id)

    if (method === 'POST' && id === undefined)
      return user ? this.createOrder() : notAuthenticated()
    if (method === 'GET' && id === undefined)
      return user ? ok(this.orderList(orders, query)) : notAuthenticated()
    if (method === 'POST' && id === 'last')
      return user ? ok({ id: orders[0]?.id ?? null }) : notAuthenticated()
    if (method === 'POST' && id === 'unpaid') {
      const unpaid = orders.find(order => order.status === STATUS_COLLECTED && !order.paid &&
        [PAYMENT_CARD, PAYMENT_TRANSFER, PAYMENT_CREDIT].includes(order.payment))
      return user ? ok({ id: unpaid?.id ?? null }) : notAuthenticated()
    }
    if (/^\d+$/.test(id ?? '') && action === undefined && ['GET', 'PUT'].includes(method)) {
      if (!user)
        return notAuthenticated()
      const order = orders.find(order => order.id === +id)
      if (order === undefined)
        return notFound()
      if (method === 'PUT') {
        for (const field of ['name', 'email', 'address', 'comment'] as const)
          if (typeof body[field] === 'string')
            order[field] = body[field]
        // adopt_order_email: a buyer without an address gets the order's one, to confirm
        const email = order.email.toLowerCase()
        if (email && !user.email && !this.users.some(other => other.email.toLowerCase() === email)) {
          Object.assign(user, { email: order.email, email_verified: false })
          this.sendEmailLink(user)
        }
      }
      return ok(this.orderJson(order))
    }
    // preorders and payments are not faked
    return undefined
  }

  private createOrder() {
    if (this.basket === null)
      return { status: 400, body: 'Basket does not exist' }
    if (this.basket.items.length === 0)
      return { status: 400, body: 'Basket is empty' }
    const order = this.addOrder({ items: this.basket.items })
    this.basket = null
    return ok(order)
  }

  private orderList(orders: FakeOrder[], query: URLSearchParams): PaginatedResult<OrderInfo> {
    const filter = query.get('filter')
    const filtered = orders.filter(order =>
      filter === 'done' ? [STATUS_DONE, STATUS_FINISHED].includes(order.status) :
        filter === 'canceled' ? order.status === STATUS_CANCELED :
          filter === 'active' ? ![STATUS_DONE, STATUS_FINISHED, STATUS_CANCELED].includes(order.status) :
            true)
    const page = Number(query.get('page') ?? 1)
    const results = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
    return {
      next: null,
      previous: null,
      count: filtered.length,
      totalPages: Math.max(Math.ceil(filtered.length / PAGE_SIZE), 1),
      currentPage: page,
      pageSize: PAGE_SIZE,
      results: results.map(({ id, total, created, status, status_text, payment, paid }) =>
        ({ id, total, created, status, status_text, payment, paid })),
    }
  }

  private respondFavorites(method: string, [action]: string[], body: Body) {
    const user = this.user
    if (method === 'GET' && action === undefined)
      return user ? ok(this.favoriteIds) : notAuthenticated()
    if (method !== 'POST' || !['add', 'remove'].includes(action))
      return undefined
    if (!user)
      return notAuthenticated()
    const product = Number(body.product)
    const favorites = this.favoriteIds.filter(id => id !== product)
    this.favorites.set(user.id, action === 'add' ? [...favorites, product] : favorites)
    return noContent()
  }

  // Answers like Serial.register for a number the backend has no orders with, so it waits for approval
  private respondSerials(method: string, [id]: string[], body: Body) {
    if (method !== 'POST' || id !== undefined)
      return undefined
    if (!this.user)
      return notAuthenticated()
    return { status: 201, body: { number: String(body.number), purchase_date: null, approved: false, product: null, order: null } }
  }

  private async product(id: number) {
    if (!this.products.has(id)) {
      const response = await this.request.get(`/api/v0/products/?id=${id}`)
      const { results } = await response.json() as PaginatedResult<ProductInfo>
      if (results.length > 0)
        this.addProducts(results[0])
    }
    return this.products.get(id)
  }

  private orderItem(product: BasketItemProduct, quantity: number): OrderItem {
    const prices = itemPrices(product, quantity)
    return { product, product_price: product.price, quantity, total: prices.price, ...prices }
  }

  private basketJson(): Basket {
    const items: BasketItem[] = this.basket!.items.map(({ id, product, quantity }) =>
      ({ id, product, quantity, ...itemPrices(product, quantity) }))
    return {
      id: this.basket!.id,
      items,
      total: items.reduce((total, item) => total + item.price, 0),
      quantity: items.reduce((quantity, item) => quantity + item.quantity, 0),
      phone: '',
      utm_source: this.basket!.utm_source,
    }
  }

  private userJson(user: FakeUser): User {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, loginCode, ...json } = user
    return json
  }

  private orderJson(order: FakeOrder): Order {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { user, ...json } = order
    return json
  }
}
