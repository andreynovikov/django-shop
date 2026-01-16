export interface ProductImage {
  src: string
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