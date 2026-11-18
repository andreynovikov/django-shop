"""
Write the OpenAPI spec that the "Sewing World API" Postman collection is generated from, see postman/README.md.

It is the drf-spectacular schema of the API with what Postman needs on top of it:

* the production server, and the storefront host for the endpoints outside /api/v0/, which drf-spectacular doesn't see;
* request names, with ⚠ in front of the operations that change production beyond the tester's session
  (the collection's pre-request script skips them unless allowSideEffects is true);
* path parameters as collection variables, such as {{productId}}, and request bodies that work as they are;
* the folders (tags) in the order of a storefront's pages.

A path parameter without a variable here fails the command, so a new endpoint can't go unnoticed.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from drf_spectacular.renderers import OpenApiJsonRenderer
from drf_spectacular.settings import spectacular_settings

API = '/api/v0'
PRODUCTION = 'https://api.sewing-world.ru'
STOREFRONT = 'https://www.sewing-world.ru'

# Path parameter → collection variable, by path template without /api/v0 and parameter name.
# The longest template that a path starts with wins.
PATH_VARIABLES = {
    ('/adverts/{id}/', 'id'): 'advertId',
    ('/baskets/{id}/', 'id'): 'basketId',
    ('/blog/categories/{id}/', 'id'): 'blogCategoryId',
    ('/blog/entries/{id}/', 'id'): 'blogEntryId',
    ('/categories/{id}/', 'id'): 'categoryId',
    ('/favorites/{id}/', 'id'): 'favoriteId',
    ('/forum/threads/{id}/', 'id'): 'forumThreadId',
    ('/forum/topics/{id}/', 'id'): 'forumTopicId',
    ('/integrations/{id}/', 'id'): 'integrationId',
    ('/integrations/{id}/byutm/', 'id'): 'integrationUtm',
    ('/kinds/{id}/', 'id'): 'kindId',
    ('/news/{id}/', 'id'): 'newsId',
    ('/orders/{id}/', 'id'): 'orderId',
    ('/pages/{url}/', 'url'): 'pageUrl',
    ('/products/{id}/', 'id'): 'productId',
    ('/products/{id}/bycode/', 'id'): 'productCode',
    ('/products/{id}/video/', 'id'): 'productCode',
    ('/products/{id}/video/qr/', 'id'): 'productId',  # by pk, unlike video/
    ('/reviews/{model}/{identifier}/', 'model'): 'reviewModel',
    ('/reviews/{model}/{identifier}/', 'identifier'): 'reviewObjectId',
    ('/reviews/{model}/{identifier}/{id}/', 'id'): 'reviewId',
    ('/reviews/{id}/', 'id'): 'reviewId',
    ('/salesactions/{slug}/', 'slug'): 'salesActionSlug',
    ('/serials/{id}/', 'id'): 'serialId',
    ('/servicecenters/{id}/', 'id'): 'serviceCenterId',
    ('/sites/{site}/', 'site'): 'siteId',
    ('/stocks/{id}/', 'id'): 'stockId',
    ('/stores/{id}/', 'id'): 'storeId',
    ('/users/{id}/', 'id'): 'userId',
    ('/users/{id}/check/', 'id'): 'phone',
    ('/warrantycard/{code}/', 'code'): 'serialNumber',
    ('/shop/user/orders/{order_id}/{template_name}/', 'order_id'): 'orderId',
    ('/kassa/payment/{order_id}/', 'order_id'): 'orderId',
    ('/kassa/receipt/{order_id}/', 'order_id'): 'orderId',
}

# Operations that change production beyond the tester's own session data, with what they do
SIDE_EFFECTS = {
    ('post', '/users/'): 'registers an account; without `code` it sends an SMS code to the phone.',
    ('put', '/users/{id}/'): 'changes the account; a new phone gets an SMS code, a new email a confirmation mail.',
    ('patch', '/users/{id}/'): 'changes the account; a new phone gets an SMS code, a new email a confirmation mail.',
    ('post', '/users/{id}/check/'): 'sends an SMS code to the phone unless the account has a permanent password '
                                    '(or `reset` is true). Throttled: 5 an hour and 10 a day per phone.',
    ('post', '/users/{id}/email-link/'): 'sends the email confirmation link again.',
    ('post', '/users/confirm-email/'): "marks the account's email as confirmed.",
    ('post', '/orders/'): 'registers a real order from the session basket: managers are notified, '
                          'and the customer gets SMS and mail in 5 minutes.',
    ('put', '/orders/{id}/'): 'changes a real order.',
    ('patch', '/orders/{id}/'): 'changes a real order.',
    ('post', '/orders/preorder/'): 'registers a real order (a stock arrival request) for the product.',
    ('post', '/orders/{id}/pay/'): 'creates a YooKassa payment for the order.',
    ('post', '/serials/'): 'registers a serial number to the account.',
    ('post', '/baskets/clear/'): 'deletes the basket of a signed link, whichever session it is in.',
    ('post', '/reviews/'): 'posts a review.',
    ('put', '/reviews/{id}/'): 'changes a review.',
    ('patch', '/reviews/{id}/'): 'changes a review.',
    ('delete', '/reviews/{id}/'): 'deletes a review.',
    ('post', '/reviews/{model}/{identifier}/'): 'posts a review.',
    ('put', '/reviews/{model}/{identifier}/{id}/'): 'changes a review.',
    ('patch', '/reviews/{model}/{identifier}/{id}/'): 'changes a review.',
    ('delete', '/reviews/{model}/{identifier}/{id}/'): 'deletes a review.',
    ('get', '/kassa/payment/{order_id}/'): 'creates a YooKassa payment for the order and redirects to its page.',
    ('post', '/kassa/callback/'): 'YooKassa notification: fetches the payment from YooKassa and updates the order.',
    ('post', '/sber/order/new'): 'SberMegaMarket notification: registers a marketplace order.',
    ('post', '/sber/order/cancel'): 'SberMegaMarket notification: cancels marketplace order items.',
}

# Operations that always answer 405, so they need no guard. postman/test.js has the same list.
NOT_ALLOWED = {
    ('put', '/baskets/{id}/'), ('patch', '/baskets/{id}/'), ('delete', '/baskets/{id}/'),
    ('post', '/favorites/'), ('put', '/favorites/{id}/'), ('patch', '/favorites/{id}/'), ('delete', '/favorites/{id}/'),
    ('delete', '/orders/{id}/'), ('delete', '/users/{id}/'),
    ('put', '/serials/{id}/'), ('patch', '/serials/{id}/'), ('delete', '/serials/{id}/'),
    ('get', '/forum/threads/'),
}

# Request bodies that work as they are, with the collection's variables
BODY_EXAMPLES = {
    ('post', '/users/login/'): {'phone': '{{phone}}', 'password': '{{password}}'},
    ('post', '/users/{id}/check/'): {'reset': False},
    ('post', '/users/'): {'phone': '{{phone}}', 'name': '', 'email': ''},
    ('patch', '/users/{id}/'): {'name': ''},
    ('post', '/users/confirm-email/'): {'token': ''},
    ('post', '/baskets/'): {},
    ('post', '/baskets/{id}/add/'): {'product': '{{productId}}', 'quantity': 1},
    ('post', '/baskets/{id}/remove/'): {'product': '{{productId}}'},
    ('post', '/baskets/{id}/update/'): {'product': '{{productId}}', 'quantity': 2},
    ('post', '/baskets/restore/'): {'contents': '{{productId}}*1'},
    ('post', '/baskets/clear/'): {'sign': ''},
    ('post', '/favorites/add/'): {'product': '{{productId}}'},
    ('post', '/favorites/remove/'): {'product': '{{productId}}'},
    ('post', '/comparisons/add/'): {'product': '{{productId}}'},
    ('post', '/comparisons/remove/'): {'product': '{{productId}}'},
    ('post', '/orders/preorder/'): {'product': '{{productId}}'},
    ('post', '/orders/{id}/pay/'): {'return_url': '{{origin}}/user/orders/'},
    ('patch', '/orders/{id}/'): {'comment': ''},
    ('post', '/serials/'): {'number': '{{serialNumber}}'},
}

# Routes of the reviews app that read the reviewed object from the query, drf-spectacular doesn't know them
REVIEW_QUERY = ('/reviews/', '/reviews/{id}/', '/reviews/average/', '/reviews/form/')
REVIEW_PARAMETERS = [
    {'name': 'model', 'in': 'query', 'required': True, 'schema': {'type': 'string'}, 'example': '{{reviewModel}}',
     'description': '`app_label.model` of the reviewed objects, such as `shop.product`'},
    {'name': 'identifier', 'in': 'query', 'required': True, 'schema': {'type': 'string'},
     'example': '{{reviewObjectId}}', 'description': 'Id of the reviewed object'},
]

OPERATIONS = ('get', 'put', 'post', 'delete', 'options', 'head', 'patch', 'trace')

TAGS = [
    ('sites', 'Site profiles. `sites/current/` is the site of the request, which comes from `X-Frontend-Key`.'),
    ('csrf', 'The CSRF token for session writes. The collection fetches it itself before each write in a session.'),
    ('users', 'Accounts, SMS codes, login and logout. A session login needs `frontendKey`: without it the API ignores '
              'the session cookie.'),
    ('categories', 'Catalog categories with their filters.'),
    ('kinds', 'Product kinds, with the fields their products are compared by.'),
    ('products', 'Products. The list takes the filters of `ProductFilterSet` (sewingworld/filters.py), ranges as '
                 '`price=a-b`; a category list and a full-text search bring the facets in `filters`.'),
    ('baskets', 'The basket of the session. It lives in the session cookie, so it needs `frontendKey`.'),
    ('favorites', 'Favorite products of the signed-in user.'),
    ('comparisons', 'Products compared in the session.'),
    ('orders', "The signed-in user's orders."),
    ('serials', 'Serial numbers registered to the signed-in user.'),
    ('warrantycard', 'Warranty card by the serial number of a sold product.'),
    ('pages', 'Flat pages of the site.'),
    ('news', 'News of the site.'),
    ('salesactions', 'Sales actions of the site and their products.'),
    ('adverts', 'Adverts (banners) of the site.'),
    ('stores', 'Shops that sell the products.'),
    ('servicecenters', 'Service centers.'),
    ('blog', 'Blog entries, categories and tags.'),
    ('forum', 'The old forum, read only.'),
    ('reviews', 'Product reviews: `reviews/shop.product/<product id>/`.'),
    ('stocks', 'Supplier stocks. Needs a token of a user with the model permission.'),
    ('integrations', 'Sales channels and the products they export. Needs a token of a user with the model permission.'),
    ('schema', 'This OpenAPI schema, as production serves it. Needs a token.'),
    ('feeds', 'Product feeds outside the API.'),
    ('documents', 'Printable pages for the signed-in owner of an order. They use the session, not the token.'),
    ('payments', 'YooKassa payments of an order. They use the session, not the token.'),
    ('webhooks', 'Notifications that YooKassa and SberMegaMarket send. All of them have side effects.'),
]

DESCRIPTION = """\
The REST API that the Sewing World storefronts call, generated from the django-shop code (drf-spectacular), \
with the endpoints outside `/api/v0/` added by hand. Production: `https://api.sewing-world.ru`.

## Setting up

Select the **Production** environment and fill in, as current values (they stay on your machine):

| Variable | What it is |
|---|---|
| `apiToken` | A DRF token (admin: *Auth Token › Tokens*). Signs every `/api/v0/` request in as its user, \
without a session. Leave it empty to call the API anonymously. |
| `frontendKey` | `SiteProfile.frontend_key` of the site to test as. Without it the API ignores the session cookie, \
takes the default site and refuses writes without `apiToken`. Baskets, comparisons and a login by phone need it. |
| `origin` | The storefront of that site, such as `https://www.sewing-world.ru`. Session writes send it as `Origin` \
for the CSRF check, so it has to be one of the backend's `ALLOWED_ORIGINS`. The endpoints outside `/api/v0/` \
(feeds, documents, payments, webhooks) are requested from it too: nginx of the API host answers 403 to anything \
but the API. |
| `phone`, `password` | For `users/login/`: a +7 phone, and the SMS code or the permanent password. |
| `allowSideEffects` | `false` by default. See below. |

## What the collection does for you

- Adds `Authorization: Token {{apiToken}}` and `X-Frontend-Key: {{frontendKey}}` to API requests when they are set.
- Before a write in a session (with `frontendKey`), gets a fresh token from `csrf/` and sends it as `X-CSRFToken`, \
with `Origin: {{origin}}`. Postman keeps the session and CSRF cookies.
- Fills the empty ID variables (`orderId`, `basketId`, `salesActionSlug`, …) from the first item of their list, \
so run a list before its detail requests. The other ID variables hold production objects; replace one that is gone. \
`serialNumber` has to be filled in by hand.
- Tests every response for a 2xx status (405 for the operations the API never allows) and, for JSON, a body \
that parses.

Without credentials, a run fails on what needs a user: 403 *Учетные данные не были предоставлены* on reads, \
and 403 *Only storefronts and token holders can change data* on every write, the 405 ones included.

## ⚠ Side effects

Requests whose names start with ⚠ change production beyond your own session: they register orders, send SMS \
and email, create payments, change accounts and reviews, or play marketplace webhooks. The collection skips them \
unless `allowSideEffects` is `true`, so a run of the whole collection is safe. Set it only for the request you mean \
to send. Basket, favorites, comparison, login and logout requests change only your own data, so they are not guarded.

Production is slow on some lists (10–30 s for `pages/`, `servicecenters/`, `salesactions/`).
"""

# The storefront serves the endpoints outside /api/v0/, nginx of the API host refuses them
STOREFRONT_SERVERS = [{
    'url': '{origin}',
    'description': 'The storefront host, which passes these paths to the backend',
    'variables': {'origin': {'default': STOREFRONT}},
}]


def text(description):
    return {'description': description}


def extra_paths():
    """ The endpoints outside /api/v0/ """
    html = {'text/html': {'schema': {'type': 'string'}}}
    login_required = {'302': text('Not signed in: redirects to the login page')}
    paths = {
        '/stock_avito.csv': {'get': {
            'operationId': 'stock_avito', 'tags': ['feeds'],
            'description': 'Stock of the products exported to Avito (`avito` flag, root category), as CSV.',
            'responses': {'200': {'description': 'CSV', 'content': {'text/csv': {'schema': {'type': 'string'}}}}},
        }},
        '/shop/user/orders/{order_id}/{template_name}/': {'get': {
            'operationId': 'order_document', 'tags': ['documents'],
            'description': 'A printable document of an order of the signed-in user, rendered from '
                           '`shop/templates/shop/order/<template_name>.html`. Needs a session login, '
                           'the token does not count here.',
            'parameters': [
                {'name': 'order_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
                {'name': 'template_name', 'in': 'path', 'required': True, 'example': 'bill', 'schema': {
                    'type': 'string', 'enum': ['bill', 'billwostamp', 'check', 'productlist', 'productlistandrules',
                                               'slip', 'slipandrules', 'warrantycards']}},
            ],
            'responses': {'200': {'description': 'HTML', 'content': html}, **login_required,
                          '404': text('No such order')},
        }},
        '/shop/warranty_card/': {'get': {
            'operationId': 'warranty_card_form', 'tags': ['documents'],
            'description': 'The form that prints a warranty card by serial number. The API has the same as '
                           '`warrantycard/{code}/`.',
            'responses': {'200': {'description': 'HTML', 'content': html}},
        }},
        '/kassa/payment/{order_id}/': {'get': {
            'operationId': 'kassa_payment', 'tags': ['payments'],
            'description': 'Creates a YooKassa payment for an order of the signed-in user and redirects to it. '
                           'The API has the same as `orders/{id}/pay/`.',
            'parameters': [{'name': 'order_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}},
                           {'name': 'return_url', 'in': 'query', 'schema': {'type': 'string'}}],
            'responses': {'302': text('To the YooKassa payment page'), '403': text('Not your order')},
        }},
        '/kassa/receipt/{order_id}/': {'get': {
            'operationId': 'kassa_receipt', 'tags': ['payments'],
            'description': 'The YooKassa receipt of a paid order of the signed-in user.',
            'parameters': [{'name': 'order_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}],
            'responses': {'200': {'description': 'The receipt, or `{}` when the order has no payment',
                                  'content': {'application/json': {'schema': {'type': 'object'}}}},
                          **login_required, '403': text('Not your order')},
        }},
        '/kassa/callback/': {'post': {
            'operationId': 'kassa_callback', 'tags': ['webhooks'],
            'description': 'YooKassa payment notification. It is not signed, so the backend fetches the payment '
                           'from YooKassa before it changes the order.',
            'requestBody': {'content': {'application/json': {'schema': {'type': 'object'}, 'example': {
                'type': 'notification', 'event': 'payment.succeeded', 'object': {'id': '', 'status': 'succeeded'}}}}},
            'responses': {'200': text('Accepted')},
        }},
        '/sber/order/new': {'post': {
            'operationId': 'sber_order_new', 'tags': ['webhooks'],
            'description': 'SberMegaMarket new order notification. Basic auth with the marketplace credentials of '
                           '`SBER_MARKET` in integrations.py.',
            'security': [{'sberAuth': []}],
            'requestBody': {'content': {'application/json': {'schema': {'type': 'object'}}}},
            'responses': {'200': text('Accepted'), '401': text('Wrong credentials')},
        }},
        '/sber/order/cancel': {'post': {
            'operationId': 'sber_order_cancel', 'tags': ['webhooks'],
            'description': 'SberMegaMarket order cancellation notification. Basic auth as for `sber/order/new`.',
            'security': [{'sberAuth': []}],
            'requestBody': {'content': {'application/json': {'schema': {'type': 'object'}}}},
            'responses': {'200': text('Accepted'), '401': text('Wrong credentials')},
        }},
    }
    for item in paths.values():
        item['servers'] = STOREFRONT_SERVERS
    return paths


def path_variable(short, name):
    """ The collection variable of a path parameter, by the longest template that the path starts with """
    for (template, parameter), variable in sorted(PATH_VARIABLES.items(), key=lambda item: -len(item[0][0])):
        if parameter == name and short.startswith(template):
            return variable
    return None


def postman_spec(schema):
    """ The drf-spectacular schema made into the spec of the Postman collection """
    spec = dict(schema)
    spec['info'] = {'title': 'Sewing World API', 'version': '0', 'description': DESCRIPTION}
    spec['servers'] = [{'url': PRODUCTION, 'description': 'Production'}]
    spec['tags'] = [{'name': name, 'description': description} for name, description in TAGS]
    spec['components']['securitySchemes']['sberAuth'] = {'type': 'http', 'scheme': 'basic'}
    spec['paths'] = {**spec['paths'], **extra_paths()}

    known_tags = {name for name, _ in TAGS}
    seen = set()
    for path, operations in spec['paths'].items():
        short = path[len(API):] if path.startswith(API + '/') else path
        for method, operation in operations.items():
            if method not in OPERATIONS:
                continue
            key = (method, short)
            seen.add(key)
            if not set(operation.get('tags', [])) <= known_tags:
                raise CommandError('%s %s has a tag that TAGS lacks: %s' % (method.upper(), path, operation.get('tags')))

            name = short.lstrip('/')
            notes = []
            if key in SIDE_EFFECTS:
                name = '⚠ ' + name
                notes.append('**⚠ Side effect on production:** %s Skipped unless `allowSideEffects` is `true`.'
                             % SIDE_EFFECTS[key])
            if key in NOT_ALLOWED:
                notes.append('Not allowed: always answers 405.')
            operation['summary'] = name
            if notes:
                operation['description'] = '\n\n'.join(notes + [operation.get('description', '')]).strip()

            for parameter in operation.get('parameters', []):
                if parameter['in'] != 'path' or 'example' in parameter:
                    continue
                variable = path_variable(short, parameter['name'])
                if variable is None:
                    raise CommandError('No collection variable for the parameter "%s" of %s, add it to PATH_VARIABLES'
                                       % (parameter['name'], path))
                parameter['example'] = '{{%s}}' % variable
            if short in REVIEW_QUERY:
                names = {parameter['name'] for parameter in operation.get('parameters', [])}
                operation['parameters'] = operation.get('parameters', []) + [
                    parameter for parameter in REVIEW_PARAMETERS if parameter['name'] not in names]
            if key in BODY_EXAMPLES:
                operation['requestBody']['content']['application/json']['example'] = BODY_EXAMPLES[key]

    missing = (set(SIDE_EFFECTS) | NOT_ALLOWED | set(BODY_EXAMPLES)) - seen
    if missing:
        raise CommandError('Operations that the API no longer has: %s'
                           % ', '.join('%s %s' % (method.upper(), path) for method, path in sorted(missing)))
    return spec


class Command(BaseCommand):
    help = 'Write the OpenAPI spec of the "Sewing World API" Postman collection, see postman/README.md'

    def add_arguments(self, parser):
        parser.add_argument('file', nargs='?', help='Where to write the spec, standard output by default')

    def handle(self, *args, **options):
        generator = spectacular_settings.DEFAULT_GENERATOR_CLASS()
        # rendered and read back, as the renderer turns the lazy strings and the like into JSON
        schema = json.loads(OpenApiJsonRenderer().render(generator.get_schema(request=None, public=True),
                                                         renderer_context={}))
        output = json.dumps(postman_spec(schema), ensure_ascii=False, indent=2) + '\n'
        if options['file']:
            with open(options['file'], 'w') as f:
                f.write(output)
        else:
            self.stdout.write(output, ending='')
