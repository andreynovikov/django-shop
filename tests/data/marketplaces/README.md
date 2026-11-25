# Marketplace OpenAPI fixtures

These snapshots contain the operations used by the marketplace HTTP mocks
and their referenced validation schemas. Tests load them locally. Each
snapshot records its source URL and SHA-256 or its upstream commit.

- `yandex_market.json` contains the four order operations used by Beru from the
  [Yandex Market Partner API specification](https://github.com/yandex-market/yandex-market-partner-api).
  Its upstream license is in [yandex_market.LICENSE](yandex_market.LICENSE).
- `ozon.json` contains FBS posting retrieval and stock updates. The
  [published Ozon schema](https://docs.ozon.ru/api/seller/swagger.json) returned
  HTTP 403 after redirects from the development environment. This snapshot uses a
  [pinned public mirror of the published schema](https://github.com/MissiaL/ozon-api/blob/2f240188c7a6fec4d4c185eb2b6bc935c2c7983b/references/ozon-seller-openapi.json).
- `wb_items.json` contains card lookup, warehouse retrieval, and stock updates
  from the [Wildberries product schema](https://dev.wildberries.ru/api/swagger/yaml/en/02-items.yaml).
- `wb_orders.json` contains new orders, order listing, and status polling
  from the [Wildberries FBS orders schema](https://dev.wildberries.ru/api/swagger/yaml/en/03-orders-fbs.yaml).

The Ozon extractor keeps RFC 3339 validation for posting dates and removes
two literal format placeholders used as regex patterns. For stock rows it
uses the documented choice of `offer_id` or `product_id` and omits the stale
requirement for the undefined `quant_size` field.

Check out the desired Yandex Market revision in a separate directory and
download the Ozon and Wildberries schema files. Regenerate the fixtures from
the backend checkout.

```sh
uv run --no-sync python tests/data/marketplaces/refresh.py yandex_market /path/to/yandex-market-partner-api
uv run --no-sync python tests/data/marketplaces/refresh.py ozon /path/to/swagger.json
uv run --no-sync python tests/data/marketplaces/refresh.py wb_items /path/to/02-items.yaml
uv run --no-sync python tests/data/marketplaces/refresh.py wb_orders /path/to/03-orders-fbs.yaml
```

If refreshing Ozon from a mirror, pass its pinned download URL with
`--source-url`. Review the generated diff and run `tests.test_beru`,
`tests.test_ozon`, and `tests.test_wb` against PostgreSQL.

Two expected failures track existing behavior. Ozon clears a stock notification
after one warehouse rejects the update, and Wildberries skips the documented
`ready_for_pickup` order status.
