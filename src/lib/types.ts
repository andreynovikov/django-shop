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