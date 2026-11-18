# Postman collection

The **Sewing World API** workspace in Postman holds a collection with every endpoint of the backend and a
**Production** environment, for testing against `https://api.sewing-world.ru`. The collection's description says
how to set it up. This folder keeps what the collection is made from:

- `sewingworld/management/commands/postman_spec.py`: the OpenAPI spec that the collection is generated from.
  It is the drf-spectacular schema with request names, ⚠ marks, path parameters as collection variables, request
  bodies and the endpoints outside `/api/v0/`.
- `prerequest.js` and `test.js`: the collection's scripts. Requests marked ⚠ change production beyond the tester's
  own session (orders, SMS, email, payments, accounts, reviews, webhooks), and `prerequest.js` skips them unless
  `allowSideEffects` is `true`. It also adds the token and the frontend key, and gets a CSRF token before writes in
  a session. `test.js` checks the status and the JSON of every response, and fills empty ID variables from lists.

## Regenerating the collection

When the API changes, the command fails if a new path parameter has no collection variable, or an operation that it
marks is gone. Add the parameter to `PATH_VARIABLES`, or update the lists, then:

1. Write the spec outside the repository:

   ```bash
   python manage.py postman_spec /tmp/sewing-world-api.json
   ```

2. In the Postman app, open the Sewing World API workspace and import the file as a Postman collection. In
   *View import settings*, set *Folder organization* to *Tags*, turn off *Enable optional parameters*, and turn on
   *Always inherit authentication*. Use the app: Postman's firewall refused part of the schema when it was sent
   through the API.
3. In the new collection, paste `prerequest.js` and `test.js` into the *Pre-request* and *Post-response* scripts,
   and copy the variables from the old collection: they hold IDs of production objects.
4. Delete the old collection.

`NOT_ALLOWED` in `test.js` is the same list as `NOT_ALLOWED` in the command; `tests/test_postman_spec.py` checks
that they match.

## Running it

Run it in the app, or with the Postman CLI:

```bash
postman collection run <collection id> -e <environment id>
```

`postman collection list --workspace <workspace id>` shows the IDs. The CLI reads the environment's shared values
only. Credentials entered as current values stay in the app, so a CLI run is anonymous unless it gets
`--env-var apiToken=…`. An anonymous run fails on everything that needs a user, as the collection's description
explains.

`api.sewing-world.ru` serves only `/api/`, and its nginx answers 403 to any other path. The collection sends the
endpoints outside the API to the storefront host, `{{origin}}`.
