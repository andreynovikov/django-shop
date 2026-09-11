export interface PaginatedResult<T> {
  next: string | null
  previous: string | null
  count: number
  totalPages: number
  currentPage: number
  pageSize: number
  results: T[]
}

export type JSONValue =
  | string
  | number
  | boolean
  | null
  | { [x: string]: JSONValue }
  | Array<JSONValue>

export interface ProductImage {
  src: string
}

export interface Category {
  id: number
  name: string
  slug: string
  svg_icon?: string
  image?: string
  children?: Category[]
}

export interface ProductInfo {
  id: number
  code: string
  article: string
  partnumber: string
  order: number
  whatis: string
  whatisit: string
  type_prefix: string
  title: string
  variations: string
  price: number
  cost: number
  discount: number
  instock: number
  image?: string
  enabled: boolean
  isnew: boolean
  recomended: boolean
  ws_pack_only: boolean
  pack_factor: number
  sales?: string[]
  sales_notes: string
  shortdescr: string
  rank?: number
  wb_link: string
  ozon_link: string
}

export interface Product {
  id: number
  code: string
  enabled: boolean
  video_url?: string
}

export interface ProductKind {
  id: number
  name: string
  comparison: string[] // keyof Product
}

export interface Country {
  id: number
  name: string
  enabled: boolean
}

export interface City {
  id: number
  country: Country
  name: string
  latitude: number | undefined
  longitude: number | undefined
  code: string
  region: number
}

export interface Store {
  id: number
  city: City
  phones: string[]
  address: string
  phone: string
  name: string
  publish: boolean
  marketplace: boolean
  lottery: boolean
  description: string
  latitude?: number
  longitude?: number
  postcode: string
  url: string
  hours: string
  logo: string
  payment_cash: boolean
  payment_visa: boolean
  payment_master: boolean
  payment_mir: boolean
  payment_credit: boolean
}

export interface ServiceCenter {
  id: number
  city: City
  address: string
  phone: string
  latitude?: number
  longitude?: number
}

export interface SalesAction {
  id: number
  name: string
  slug: string
  show_products: boolean
  description: string
  image: string | undefined
  image_width: number | undefined
  image_height: number | undefined
}

export interface Serial {
  number: string
  approved: boolean
  purchase_date?: string
  product?: unknown
  order?: unknown
}

export interface User {
  id: number | null
  is_anonymous: boolean
  phone: string
  name: string
  full_name: string
  gravatar: string
  username: string
  email: string
  postcode: string
  city: string
  address: string
  discount: number
  bonuses: number
  expiring_bonuses: number
  expiration_date: string | null
  permanent_password: boolean
  last_login: string
  date_joined: string
}

export interface UserEdit {
  name: string
  phone: string
  email: string
  address: string
  username: string
}

export interface UserForm {
  name: string
  label: string
  id: string
  required: boolean

}[]

export interface UserCheck {
  phone: string
  permanent_password: boolean
}

export interface UserBonus {
  value: number
  is_fresh: boolean
  is_undefined: boolean
  is_updating: boolean
}

export interface FlatPageInfo {
  url: string
  title: string
}

export interface FlatPage {
  id: number
  url: string
  title: string
  content: string
  template_name: string
  enable_comments: boolean
  registration_required: boolean
}

interface ForumOpinion {
  id: number
  post: string
  text: string
}

interface ForumThreadBase {
  id: number
  title: string
  mtime?: string | null
}

export interface ForumThread extends ForumThreadBase {
  opinions: ForumOpinion[]
}

export interface ForumTopic {
  id: number
  title: string
  threads: ForumThreadBase[]
}

export interface Integration {
  id: number
  name: string
  utm_source: string
  enabled: boolean
  output_template: string
  output_all: boolean
  output_paged: boolean
  output_available: boolean
  output_with_images: boolean
  output_stock: boolean
  output_skip_categories: boolean
  uses_api: boolean
  uses_boxes: boolean
  settings?: JSONValue
  admin_user_fields?: JSONValue
  site: number
  seller?: number
  buyer?: number
  wirehouse?: number
}

export interface IntegrationProduct {
  id: number
  code: string
  article: string
  partnumber: string
  whatisit: string
  title: string
  price: number
  enabled: boolean
  stock?: number
}