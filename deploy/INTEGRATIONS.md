# Integration deployment

## Yandex Market FBS orders

Enabled API integrations with `ym_campaign` use their stored `api_key` to
discover the Market business ID. Give the key order-processing access in the
Market cabinet and enable boxes on the integration for packing in Django.
Confirm the source site has a profile and the Beru system user (`0000`) exists.

After deploying `main`, restart uWSGI and reload the Celery workers. Run the
order dispatcher once from the production backend checkout.

```sh
sudo systemctl restart uwsgi@prod uwsgi@admin
sudo systemctl reload celery@prod
uv run --no-sync celery -A sewingworld call beru.tasks.get_orders
```

Check that the per-integration tasks succeeded and compare the **New** orders
and statuses with the Market cabinet. Then add `beru.tasks.get_orders` to
Celery Beat in Django admin with a 15-minute interval. Use the Market cabinet
for shipment confirmation after orders are ready to ship.
