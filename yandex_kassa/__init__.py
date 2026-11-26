from yookassa import Configuration


def configure_yookassa(order):
    """
    Points the YooKassa SDK, whose configuration is global, at the shop account of the order's site, or of the
    order's seller when the site has none.
    """
    if order.site.profile.yookassa_id:
        Configuration.account_id = order.site.profile.yookassa_id
        Configuration.secret_key = order.site.profile.yookassa_key
    else:
        Configuration.account_id = order.seller.yookassa_id
        Configuration.secret_key = order.seller.yookassa_key
