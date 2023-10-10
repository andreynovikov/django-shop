// Must be synced with Order model
export const STATUS_NEW = 0x0
export const STATUS_ACCEPTED = 0x00000001
export const STATUS_WAITING = 0x00000002
export const STATUS_COLLECTING = 0x00000004
export const STATUS_CANCELED = 0x00000008
export const STATUS_FROZEN = 0x00000010
export const STATUS_OTHERSHOP = 0x00000020
export const STATUS_COLLECTED = 0x00000040
export const STATUS_SERVICE = 0x00000080
export const STATUS_DELIVERED_SHOP = 0x00000100
export const STATUS_DELIVERED_STORE = 0x00000200
export const STATUS_SENT = 0x00000400
export const STATUS_DELIVERED = 0x00000800
export const STATUS_CONSULTATION = 0x00001000
export const STATUS_PROBLEM = 0x00002000
export const STATUS_DONE = 0x00004000
export const STATUS_RETURNING = 0x02000000
export const STATUS_UNCLAIMED = 0x04000000
export const STATUS_FINISHED = 0x0F000000

export const PAYMENT_CASH = 1
export const PAYMENT_CARD = 2
export const PAYMENT_TRANSFER = 3
export const PAYMENT_COD = 4
export const PAYMENT_POS = 5
export const PAYMENT_CREDIT = 6
export const PAYMENT_UNKNOWN = 99

export const DELIVERY_COURIER = 1
export const DELIVERY_CONSULTANT = 2
export const DELIVERY_SELF = 3
export const DELIVERY_TRANSPORT = 4
export const DELIVERY_PICKPOINT = 5
export const DELIVERY_YANDEX = 6
export const DELIVERY_TRANSIT = 7
export const DELIVERY_POST = 8
export const DELIVERY_OZON = 9
export const DELIVERY_INTEGRAL = 10
export const DELIVERY_BOXBERRY = 11
export const DELIVERY_EXPRESS = 98
export const DELIVERY_UNKNOWN = 99

const getColor = (status) => {
    // badge colors from https://demo.createx.studio/cartzilla/components/badge.html
    // 'danger' is currently unused
    switch (status) {
        case STATUS_NEW:
            return 'info';
        case STATUS_ACCEPTED:
        case STATUS_COLLECTING:
        case STATUS_COLLECTED:
        case STATUS_OTHERSHOP:
        case STATUS_SENT:
        case STATUS_DELIVERED_STORE:
            return 'danger';
        case STATUS_DELIVERED:
        case STATUS_DELIVERED_SHOP:
            return 'primary';
        case STATUS_DONE:
        case STATUS_FINISHED:
            return 'success';
        case STATUS_PROBLEM:
        case STATUS_UNCLAIMED:
        case STATUS_SERVICE:
            return 'warning';
        case STATUS_FROZEN:
        case STATUS_CONSULTATION:
        case STATUS_RETURNING:
            return 'dark';
        case STATUS_CANCELED:
            return 'secondary';
        default:
            return 'light';
    }
};

export default function OrderStatusBadge({status, text}) {
    return <span className={"badge bg-" + getColor(status) + " fs-sm"}>{ text }</span>
}
