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

// Messages and status codes follow django-shop: sewingworld/api.py and sewingworld/serializers.py
const NOT_AUTHENTICATED = 'Учетные данные не были предоставлены.'
const PERMISSION_DENIED = 'У вас недостаточно прав для выполнения данного действия.'
const NOT_FOUND = 'Не найдено.'
const PHONE_TAKEN = 'Пользователь с указанным номером уже зарегестрирован'
const EMAIL_TAKEN = 'Пользователь с указанным адресом уже зарегестрирован'
const USERNAME_TAKEN = 'Пользователь с указанным псевдонимом уже зарегестрирован'

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

export interface FakeUser extends User {
  password?: string // the last SMS code, or the permanent password
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

export function normalizePhone(phone: string) {
  const digits = phone.replaceAll(/\D/g, '')
  return '+7' + (digits.length === 11 ? digits.slice(1) : digits)
}

function toBasketProduct(product: ProductInfo | BasketItemProduct): BasketItemProduct {
  return {
    id: product.id,
    code: product.code,
    title: product.title,
    whatis: product.whatis ?? '',
    partnumber: product.partnumber ?? '',
    article: product.article ?? '',
    image: product.image ?? '',
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

  private users: FakeUser[] = []
  private sessionUserId: number | null = null
  private basket: { id: number, items: { id: number, product: BasketItemProduct, quantity: number }[] } | null = null
  private favorites = new Map<number, number[]>()
  private orders: FakeOrder[] = []
  private products = new Map<number, BasketItemProduct>()
  private nextId = { user: 1, basket: 1, item: 1, order: 100001 }

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
      is_anonymous: false,
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
      last_login: '',
      date_joined: '',
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

  get basketItems() {
    return this.basket?.items.map(({ product, quantity }) => ({ product: product.id, quantity })) ?? []
  }

  get favoriteIds() {
    return this.sessionUserId === null ? [] : this.favorites.get(this.sessionUserId) ?? []
  }

  lastOrder() {
    return this.orders.at(-1)
  }

  lastSmsCode(phone: string) {
    const normalized = normalizePhone(phone)
    return this.smsLog.findLast(sms => sms.phone === normalized)?.code
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
    }
    return undefined
  }

  private respondUsers(method: string, [key, action]: string[], body: Body) {
    if (method === 'GET' && key === 'current')
      return ok(this.user ? this.userJson(this.user) : { id: null, is_anonymous: true } as AnonymousUser)
    if (method === 'GET' && key === 'logout') {
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
    if (/^\d+$/.test(key ?? '') && action === undefined) {
      if (this.user?.id !== +key)
        return { status: 403, body: { detail: PERMISSION_DENIED } }
      if (method === 'GET')
        return ok(this.userJson(this.user))
      if (method === 'PUT')
        return this.updateUser(this.user, body)
    }
    // users/form/ and the like are the same for everybody, so they come from the backend
    return undefined
  }

  private register(body: Body) {
    const phone = normalizePhone(String(body.phone ?? ''))
    const email = String(body.email ?? '')
    const username = String(body.username ?? '')
    const errors = this.uniqueErrors(undefined, phone, email, username)
    if (Object.keys(errors).length > 0)
      return { status: 400, body: errors }
    const user = this.addUser({ phone, email, username, name: String(body.name ?? '') })
    return { status: 201, body: this.userJson(user) }
  }

  // Starts an SMS login, the code is in smsLog instead
  private check(phone: string, body: Body) {
    const user = this.findUser(phone)
    if (user === undefined)
      return notFound()
    const permanent = user.permanent_password
    const reset = Boolean(body.reset)
    if (!permanent || reset) {
      const code = String(1000 + Math.floor(Math.random() * 9000))
      user.password = code
      user.permanent_password = false
      this.smsLog.push({ phone: user.phone, code })
    }
    return ok({ phone: user.phone, permanent_password: permanent && !reset })
  }

  private login(body: Body) {
    const phone = normalizePhone(String(body.phone ?? ''))
    let user = this.findUser(phone)
    let registered = false
    if (user === undefined && ['order', 'preorder', 'warranty'].includes(String(body.ctx))) {
      // the backend silently registers a buyer, without sending a code
      user = this.addUser({ phone, name: '', username: '' })
      registered = true
    } else if (user === undefined || !body.password || body.password !== user.password) {
      return notAuthenticated()
    }
    if (typeof body.permanent_password === 'string' && body.permanent_password.length > 0) {
      user.password = body.permanent_password
      user.permanent_password = true
    }
    this.sessionUserId = user.id
    return ok({ id: user.id, registered })
  }

  private updateUser(user: FakeUser, body: Body) {
    const phone = normalizePhone(String(body.phone ?? user.phone))
    const email = String(body.email ?? user.email)
    const username = String(body.username ?? user.username)
    const errors = this.uniqueErrors(user, phone, email, username)
    if (Object.keys(errors).length > 0)
      return { status: 400, body: errors }
    const name = String(body.name ?? user.name)
    Object.assign(user, { name, full_name: name, phone, email, username, address: String(body.address ?? user.address) })
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
      this.basket ??= { id: this.nextId.basket++, items: [] }
      return { status: 201, body: this.basketJson() }
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
      if (method === 'PUT')
        for (const field of ['name', 'email', 'address', 'comment'] as const)
          if (typeof body[field] === 'string')
            order[field] = body[field]
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
      utm_source: '',
    }
  }

  private userJson(user: FakeUser): User {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { password, ...json } = user
    return json
  }

  private orderJson(order: FakeOrder): Order {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { user, ...json } = order
    return json
  }
}
