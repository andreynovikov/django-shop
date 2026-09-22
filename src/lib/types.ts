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
  article: string
  partnumber: string
  title: string
  price: number
  cost: number
  enabled: boolean
  video_url?: string
  // TODO - add remaining fields
}

export interface ProductKind {
  id: number
  name: string
  comparison: string[] // keyof Product
}

export interface ProductStock {
  product: string
  supplier: string
  quantity: number
  correction: number
  reason: string
}

export interface ProductReview {
  id: number
  advantage: string
  disadvantage: string
  comment: string
  weight: number
  user: {
    id: string
    full_name: string
    gravatar: string
  }
  reviewer_name: string
  reviewer_avatar: string
  site: number
  submit_date: string
  is_public: boolean
  rating: {
    value: number
    text: string
  }
}

export interface ProductReviewFormField {
  name: string
  label: string
  help: string
  class: string
  widget: string
  required: boolean
  choices?: unknown
  attrs?: unknown
  value?: unknown
}

export type ProductReviewForm = Array<ProductReviewFormField>

export interface BasketItemProduct {
  id: number
  code: string
  title: string
  whatis: string
  partnumber: string
  article: string
  image: string
  ws_pack_only: boolean
  pack_factor: number
  price: number
  cost: number
}

export interface BasketItem {
  id: number
  product: BasketItemProduct
  price: number
  quantity: number
  cost: number
  discount: number
  discount_text: string
}

export interface Basket {
  id: number
  items: BasketItem[]
  total: number
  quantity: number
  phone: string
  utm_source: string
}

export interface OrderInfo {
  id: number
  total: number
  created: string
  status: number
  status_text: string
  payment: number
  paid: boolean
}

export interface OrderItem {
  product: BasketItemProduct
  cost: number
  discount: number
  discount_text: string
  price: number
  product_price: number
  quantity: number
  total: number
}

export interface Order {
  id: number
  created: string
  status: number
  status_text: string
  payment: number
  payment_text: string
  paid: boolean
  total: number
  delivery: number
  delivery_price: number
  delivery_tracking_number: string
  delivery_info: string
  delivery_dispatch_date: string | null
  delivery_handing_date: string | null
  delivery_time_from: string | null
  delivery_time_till: string | null
  store: number | null
  name: string
  phone: string
  email: string
  address: string
  is_firm: boolean
  firm_name: string
  firm_address: string
  firm_details: string
  comment: string
  items: OrderItem[]
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

export interface UserFormField {
  name: string
  label: string
  id: string
  required: boolean
}

export type UserForm = Array<UserFormField>

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

export interface Site {
  id: number
  url_prefix: string
  title: string
  description: string
  phone: string
  city?: City
}

export interface Advert {
  id: number
  name: string
  place: string
  categories: number[]
  image: string | null
  big_image: string | null
  content: string
  order: number
}

export interface News {
  id: number
  title: string
  image: string | null
  image_width: number | null
  image_height: number | null
  content: string
  publish_date: string
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