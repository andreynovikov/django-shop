# Integration deployment

## Yandex.Market FBS orders

Enabled API integrations with `ym_campaign` use their stored `api_key` to
discover the Market business ID. Give the key order-processing access in the
Market cabinet and enable boxes on the integration for packing in Django.
Confirm the source site has a profile and the Yandex.Market system user (`0000`) exists.

After deploying `main`, restart uWSGI and reload the Celery workers. Run the
order dispatcher once from the production backend checkout.

```sh
sudo systemctl restart uwsgi@prod uwsgi@admin
sudo systemctl reload celery@prod
uv run --no-sync celery -A sewingworld call ym.tasks.get_orders
```

Check that the per-integration tasks succeeded and compare the **New** orders
and statuses with the Market cabinet. Then add `ym.tasks.get_orders` to
Celery Beat in Django admin with a 15-minute interval. Use the Market cabinet
for shipment confirmation after orders are ready to ship.

### Yandex.Market API notifications

Apply the Ansible `nginx` tag after deploying to route the callback on
`api.sewing-world.ru`. Keep the order polling schedule enabled to reconcile
missed notifications.

Generate a separate secret for each store and add it as `push_token` to the
integration's existing JSON settings in Django admin.

```sh
uv run --no-sync python -c 'from secrets import token_urlsafe; print(token_urlsafe(32))'
```

Use the integration's numeric ID from its Django admin URL and keep the full
callback URL private.

```text
https://api.sewing-world.ru/integrations/ym/<integration-id>/notification?token=<push-token>
```

In the seller cabinet, go to **Settings → APIs and modules → API notifications**.
Register the full URL for the store whose campaign ID is configured in
`ym_campaign`. Select `ORDER_CREATED`, `ORDER_CANCELLED`, `ORDER_STATUS_UPDATED`,
and `ORDER_UPDATED`. Confirm the connection check, then check the result of
`ym.tasks.sync_integration_order` in Celery after the first order event.
[Yandex.Market notification setup](https://yandex.ru/dev/market/partner-api/doc/en/push-notifications/)

## Ozon FBS push notifications

After deploying `main`, restart the public uWSGI app and reload the Celery
workers from the production backend checkout.

```sh
sudo systemctl restart uwsgi@prod
sudo systemctl reload celery@prod
```

Apply the Ansible `nginx` tag to the production server to route the
callback on `api.sewing-world.ru` to Django. The callback checks the
connecting IP against Ozon's published ranges.

For each enabled Ozon FBS integration, generate a separate secret.

```sh
uv run --no-sync python -c 'from secrets import token_urlsafe; print(token_urlsafe(32))'
```

Add it as `push_token` in the integration's existing JSON settings in Django
admin. Use the integration's numeric ID from its admin URL to build the
callback URL. Keep the full URL private.

```text
https://api.sewing-world.ru/integrations/ozon/notifications/<integration-id>/?token=<push-token>
```

Callbacks registered under `/ozon/` also work.

In [Ozon Seller's notification settings](https://seller.ozon.ru/app/settings/notifications-api),
add the callback, run the connection check, and subscribe to
`TYPE_NEW_POSTING`, `TYPE_STATE_CHANGED`, `TYPE_POSTING_CANCELLED`,
`TYPE_CUTOFF_DATE_CHANGED`, and `TYPE_DELIVERY_DATE_CHANGED`. Check the
result of `ozon.tasks.sync_integration_posting` in Celery after the first event
and compare the local order with the posting in Ozon.

Keep the existing `ozon.tasks.get_unfulfilled_orders` schedule enabled so
polling can catch missed notifications. With `push_token` configured, polling
also reconciles delivery statuses and cancellations in its seven-day window.
