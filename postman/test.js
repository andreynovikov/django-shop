// Sewing World API: checks for every response, and the ID variables filled from lists
const NOT_ALLOWED = [  // operations that always answer 405, as NOT_ALLOWED in sewingworld/management/commands/postman_spec.py
    'PUT baskets/{id}/', 'PATCH baskets/{id}/', 'DELETE baskets/{id}/',
    'POST favorites/', 'PUT favorites/{id}/', 'PATCH favorites/{id}/', 'DELETE favorites/{id}/',
    'DELETE orders/{id}/', 'DELETE users/{id}/',
    'PUT serials/{id}/', 'PATCH serials/{id}/', 'DELETE serials/{id}/',
    'GET forum/threads/',
];
// Empty variables that the first item of a list fills: [method and path, variable, field]
const CAPTURE = [
    [/^GET \/api\/v0\/news\/$/, 'newsId', 'id'],
    [/^GET \/api\/v0\/salesactions\/$/, 'salesActionSlug', 'slug'],
    [/^GET \/api\/v0\/orders\/$/, 'orderId', 'id'],
    [/^GET \/api\/v0\/baskets\/$/, 'basketId', 'id'],
    [/^GET \/api\/v0\/integrations\/$/, 'integrationId', 'id'],
    [/^GET \/api\/v0\/integrations\/$/, 'integrationUtm', 'utm_source'],
    [/^GET \/api\/v0\/reviews\/[^/]+\/[^/]+\/$/, 'reviewId', 'id'],
];

const operation = `${pm.request.method} ${pm.info.requestName}`;
if (NOT_ALLOWED.includes(operation)) {
    pm.test('Status is 405, as the API does not allow it', () => pm.response.to.have.status(405));
} else {
    pm.test('Status is 2xx', () => pm.expect(pm.response.code).to.be.within(200, 299));
}

if ((pm.response.headers.get('Content-Type') || '').includes('application/json') && pm.response.text()) {
    let body;
    pm.test('Body is JSON', () => { body = pm.response.json(); });
    const key = `${pm.request.method} ${pm.request.url.getPath()}`;
    if (body !== undefined && pm.response.code === 200) {
        const first = Array.isArray(body) ? body[0] : (Array.isArray(body.results) ? body.results[0] : undefined);
        CAPTURE.forEach(([pattern, variable, field]) => {
            if (pattern.test(key) && first && first[field] !== undefined && !pm.variables.get(variable)) {
                pm.collectionVariables.set(variable, String(first[field]));
            }
        });
    }
    // A new basket is the session's basket from now on
    if (key === 'POST /api/v0/baskets/' && body && body.id) {
        pm.collectionVariables.set('basketId', String(body.id));
    }
}
