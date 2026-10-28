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

interface CategoryBreadcrumb {
  id: number
  slug: string
  name: string
}

export interface CategoryFilter {
  name: string
  id: string
  class: string
  label: string
  widget: string
}

export interface CategoryTreeItem {
  id: number
  name: string
  subname: string
  active: boolean
  hidden: boolean
  feed: boolean
  slug: string
  svg_icon?: string
  image?: string
  children?: Array<CategoryTreeItem>
}

export type CategoryTree = Array<CategoryTreeItem>

interface CategoryBrief {
  id: number
  name: string
  slug: string
  path: {
    uri: string
    breadcrumbs: Array<CategoryBreadcrumb>
  }
}

export interface Category {
  id: number
  name: string
  subname?: string
  slug: string
  description?: string
  svg_icon?: string
  image?: string
  product_order?: string
  path: {
    uri: string
    breadcrumbs: Array<CategoryBreadcrumb>
  }
  filters?: Array<CategoryFilter>
  children?: Array<CategoryTreeItem>
}

// Choices and ranges of a category filter for the current product list
export interface ProductFilter {
  id: string
  choices?: Array<[string | number, string]>
  attrs?: {
    step?: number
    min_value?: number
    max_value?: number
  }
}

export type ProductList = PaginatedResult<ProductInfo> & {
  filters?: Record<string, ProductFilter>
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
  gtin: string
  gtins: Array<string>
  tnved: string
  enabled: boolean
  title: string
  cost: number
  price: number
  ws_price: number
  ws_pack_only: boolean
  pct_discount: number
  val_discount: number
  ws_pct_discount: number
  max_val_discount: number
  discount: number
  image?: string
  big_image?: string
  images: ProductImage[]
  kind?: Array<number>
  categories: Array<CategoryBrief>
  tags: string
  service_life: number
  warranty: number
  extended_warranty: string
  manufacturer_warranty: boolean
  comment_warranty: string

  accessories?: Array<ProductInfo>
  similar?: Array<ProductInfo>
  gifts?: Array<ProductInfo>
  sales?: Array<SalesAction>
  instock: number

  swcode: string
  runame: string
  sales_notes: string
  gift: boolean
  merchant: boolean
  wb_link: string
  ozon_link: string
  manufacturer: Manufacturer
  country: Country
  developer_country: Country
  certificate: string
  isnew: boolean
  deshevle: boolean
  recomended: boolean
  absent: boolean
  credit_allowed: boolean
  present: string
  coupon: boolean
  not_for_sale: boolean
  suspend: boolean
  preorder: boolean
  order: number
  opinion: string
  allow_reviews: boolean
  measure: string
  weight: number
  length: number
  width: number
  height: number
  delivery: number
  consultant_delivery_price: number
  spec: string
  descr: string
  state: string
  manuals: string
  stitches: string
  complect: string
  dealertxt: string
  video_url: string
  pack_factor: number
  shortdescr: string
  seodescr: string
  yandexdescr: string
  type_prefix: string
  whatis: string
  whatisit: string
  variations: string
  comment_packer: string

  constituents?: Array<ProductInfo>
  hide_contents: boolean

  fabric_verylite: string
  fabric_lite: string
  fabric_medium: string
  fabric_hard: string
  fabric_veryhard: string
  fabric_stretch: string
  fabric_leather: string
  sm_shuttletype: string
  sm_stitchwidth: string
  sm_stitchlenght: string
  sm_stitchquantity: number
  sm_buttonhole: string
  sm_dualtransporter: string
  sm_platformlenght: string
  sm_freearm: string
  ov_freearm: string
  sm_feedwidth: string
  sm_footheight: string
  sm_constant: string
  sm_speedcontrol: string
  sm_needleupdown: string
  sm_threader: string
  sm_spool: string
  sm_presscontrol: string
  sm_power: number
  sm_light: string
  sm_organizer: string
  sm_autostop: string
  sm_ruler: string
  sm_wastebin: string
  sm_cover: string
  sm_startstop: string
  sm_kneelift: string
  sm_display: string
  sm_advisor: string
  sm_memory: string
  sm_mirror: string
  sm_fix: string
  sm_alphabet: string
  sm_diffeed: string
  sm_easythreading: string
  sm_needles: string
  sm_software: string
  sm_autocutter: string
  sm_maxi: string
  sm_autobuttonhole_bool: boolean
  sm_threader_bool: boolean
  sm_dualtransporter_bool: boolean
  sm_alphabet_bool: boolean
  sm_maxi_bool: boolean
  sm_patterncreation_bool: boolean
  sm_advisor_bool: boolean
  km_class: string
  km_font: string
  km_needles: string
  km_prog: string
  km_rapport: string
  sw_hoopsize: string
  sw_datalink: string
  prom_transporter_type: string
  prom_shuttle_type: string
  prom_speed: string
  prom_needle_type: string
  prom_stitch_lenght: string
  prom_foot_lift: string
  prom_fabric_type: string
  prom_oil_type: string
  prom_weight: number
  prom_cutting: string
  prom_threads_num: string
  prom_power: string
  prom_bhlenght: string
  prom_overstitch_lenght: string
  prom_overstitch_width: string
  prom_stitch_width: string
  prom_needle_width: string
  prom_needle_num: string
  prom_platform_type: string
  prom_button_diaouter: string
  prom_button_diainner: string
  prom_needle_height: string
  prom_stitch_type: string
  prom_autothread: string
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
  instock: number
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

export interface Manufacturer {
  id: number
  code: string
  name: string
  machinemaker: boolean
  accessorymaker: boolean
  logo: string
  logo_width?: number
  logo_height?: number
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
  address2: string
  phone: string
  phone2: string
  name: string
  pickuponly: boolean
  publish: boolean
  marketplace: boolean
  lottery: boolean
  description: string
  latitude?: number
  longitude?: number
  postcode: string
  url: string
  email: string
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

export interface AnonymousUser {
  id: null
  is_anonymous: true
  name: undefined
}

export interface UserInfo {
  id: number
  full_name: string
  gravatar: string
}

export interface User {
  id: number
  is_anonymous: false
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
  name: keyof UserEdit
  label: string
  id: string
  required: boolean
  help?: string
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

interface BlogEntryBase {
  author: UserInfo
  urls: {
    canonical: string
    short: string
  }
  tags: Array<string>
}

export interface BlogEntryNavigation extends BlogEntryBase {
  title: string
}

export interface BlogEntryInfo extends BlogEntryBase {
  id: number
  title: string
  slug: string
  publication_date: string
  created: string
  modified: string
  content: {
    preview: string
    total_words: number
    remaining_words: number
    remaining_percent: number
  }
  image: string
  image_width?: number
  image_height?: number
  image_caption: string
  related: Array<number>
  featured: boolean
  categories: Array<number>
  tags: Array<string>
}

export interface BlogEntry extends BlogEntryBase {
  id: number
  title: string
  slug: string
  publication_date: string
  created: string
  modified: string
  content: string
  image: string
  image_width?: number
  image_height?: number
  image_caption: string
  related: Array<number>
  featured: boolean
  categories: Array<number>
  tags: Array<string>
  navigation: {
    previous: BlogEntryNavigation | null
    next: BlogEntryNavigation | null
  }
}

export interface BlogTag {
  name: string
  count: number
}

export interface BlogCloudTag {
  name: string
  count: number
  weight: number
}

export interface BlogCategory {
  id: number
  title: string
  slug: string
  count: number
}