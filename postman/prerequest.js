// Sewing World API: the production guard, credentials and CSRF. The collection's description explains them.
const requestName = pm.info.requestName || '';
const guarded = requestName.startsWith('⚠') && String(pm.variables.get('allowSideEffects')) !== 'true';

if (guarded) {
    console.warn(`Skipped "${requestName}": it changes production. Set allowSideEffects to true to send it.`);
    pm.execution.skipRequest();
} else {
    const isApi = pm.request.url.getPath().startsWith('/api/v0/');
    const frontendKey = pm.variables.get('frontendKey');
    const apiToken = pm.variables.get('apiToken');

    // The requests have no auth of their own, so nothing replaces these headers
    if (isApi && apiToken) {
        pm.request.headers.upsert({ key: 'Authorization', value: `Token ${apiToken}` });
    }
    if (isApi && frontendKey) {
        pm.request.headers.upsert({ key: 'X-Frontend-Key', value: frontendKey });
    }

    // With the key, the API reads the session cookie, and Django checks CSRF on writes of a signed-in session.
    // Login rotates the token, so a fresh one comes from csrf/ before every write; Postman keeps the cookies.
    if (isApi && frontendKey && !['GET', 'HEAD', 'OPTIONS'].includes(pm.request.method)) {
        const origin = pm.variables.get('origin');
        if (origin) {
            pm.request.headers.upsert({ key: 'Origin', value: origin });
        }
        pm.sendRequest({
            url: pm.variables.replaceIn('{{baseUrl}}') + '/api/v0/csrf/',
            method: 'GET',
            header: { 'X-Frontend-Key': frontendKey },
        }, (error, response) => {
            if (error || response.code !== 200) {
                console.error('No CSRF token from csrf/:', error || response.code);
                return;
            }
            pm.request.headers.upsert({ key: 'X-CSRFToken', value: response.json().csrf });
        });
    }
}
