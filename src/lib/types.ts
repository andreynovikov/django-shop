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

export interface Product {
  id: number
  code: string
  enabled: boolean
  video_url?: string
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
  latitude: number
  longitude: number
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