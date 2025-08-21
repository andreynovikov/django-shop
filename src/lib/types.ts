export interface ProductImage {
    src: string,
    thumbnail: {
        src: string,
        width: number,
        height: number
    }
}

export interface Serial {
    number: string,
    approved: boolean,
    purchase_date?: string,
    product?: unknown,
    order?: unknown
}

export interface UserBonus {
    value: number,
    is_fresh: boolean,
    is_undefined: boolean,
    is_updating: boolean
}