"""HTTP mocks backed by local marketplace OpenAPI snapshots."""
import json
from collections import deque
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator


def load_spec(path):
    return json.loads((Path(__file__).parent / 'data' / path).read_text(encoding='utf-8'))


def resolve(spec, definition):
    if '$ref' not in definition:
        return definition
    ref = definition['$ref']
    if not ref.startswith('#/'):
        raise ValueError(f'Expected a local reference, got {ref!r}')
    target = spec
    for part in ref[2:].split('/'):
        target = target[part.replace('~1', '/').replace('~0', '~')]
    return resolve(spec, target)


def validate_json(spec, validator_class, definition, payload):
    content = resolve(spec, definition)['content']
    schema = next(value['schema'] for media_type, value in content.items()
                  if media_type == 'application/json' or media_type.endswith('+json'))
    validator = validator_class(spec, format_checker=validator_class.FORMAT_CHECKER)
    validator.evolve(schema=schema).validate(payload)


class OpenAPIMock:
    """
    Check the actual wire request and validate each JSON response before serving it.

    It stands in for urlopen: each call must be the next request queued with expect(), and a request left unmade
    fails the test. Requests and responses are validated against the operation in the bundled schema.
    """

    def __init__(self, test, headers):
        self.test = test
        self.headers = headers
        self.pending = deque()
        self.test.addCleanup(self.assert_consumed)

    def assert_consumed(self):
        self.test.assertEqual([call[2] for call in self.pending], [], 'Expected API requests were not made')

    def expect(self, spec, path, method, response, *, body=None, query=None, status=200, path_params=None):
        path_item = spec['paths'][path]
        operation = path_item[method.lower()]
        servers = operation.get('servers') or path_item.get('servers') or spec['servers']
        server = servers[0]['url']
        if server.startswith('//'):
            server = 'https:' + server
        url = server.rstrip('/') + path.format(**(path_params or {}))
        self.pending.append((spec, operation, url, method, response, body, query or {}, status))

    def __call__(self, request, **kwargs):
        self.test.assertTrue(self.pending, f'Unexpected request to {request.full_url}')
        spec, operation, url, method, response, body, query, status = self.pending.popleft()
        actual_url = urlsplit(request.full_url)
        self.test.assertEqual((request.get_method(), actual_url._replace(query='').geturl()), (method, url))
        self.test.assertEqual(parse_qs(actual_url.query), query)
        # urllib.request.Request keeps header names as str.capitalize() makes them, such as Api-key
        for name, value in self.headers.items():
            self.test.assertEqual(request.get_header(name.capitalize()), value)
        if 'timeout' in kwargs:
            self.test.assertGreater(kwargs['timeout'], 0)

        if body is None:
            self.test.assertIsNone(request.data)
        else:
            self.test.assertEqual(request.get_header('Content-type').split(';', 1)[0].strip(), 'application/json')
            actual = json.loads(request.data)
            validate_json(spec, OAS30WriteValidator, operation['requestBody'], actual)
            self.test.assertEqual(actual, body)

        definition = resolve(spec, operation['responses'][str(status)])
        if isinstance(response, bytes):  # An intentionally malformed response.
            encoded = response
        elif 'content' in definition:
            validate_json(spec, OAS30ReadValidator, definition, response)
            encoded = json.dumps(response).encode()
        else:
            self.test.assertIsNone(response)
            encoded = b''

        stream = BytesIO(encoded)
        if status >= 400:
            raise HTTPError(request.full_url, status, 'Marketplace error', {}, stream)
        return stream
