"""
Bundle the API operations used by the marketplace tests.

Writes <marketplace>.json next to this file: only the operations listed below and the components they reference,
without documentation and vendor extensions, with the source URL and hash or the upstream commit recorded. Yandex
Market is read from a checkout of its API repository, whose LICENSE is copied alongside.
"""
import argparse
import hashlib
import json
from pathlib import Path
from shutil import copyfile
from subprocess import check_output

import yaml


SOURCES = {
    'ozon': (
        'https://docs.ozon.ru/api/seller/swagger.json',
        {'/v4/posting/fbs/list': 'post', '/v3/posting/fbs/get': 'post', '/v2/products/stocks': 'post'},
    ),
    'wb_items': (
        'https://dev.wildberries.ru/api/swagger/yaml/en/02-items.yaml',
        {'/content/v2/get/cards/list': 'post', '/api/v3/warehouses': 'get', '/api/v3/stocks/{warehouseId}': 'put'},
    ),
    'wb_orders': (
        'https://dev.wildberries.ru/api/swagger/yaml/en/03-orders-fbs.yaml',
        {'/api/v3/orders/new': 'get', '/api/v3/orders': 'get', '/api/v3/orders/status': 'post'},
    ),
}
YANDEX_OPERATIONS = {
    'yandex_market': {
        '/v2/campaigns/{campaignId}': 'get',
        '/v1/businesses/{businessId}/orders': 'post',
        '/v2/campaigns/{campaignId}/orders/{orderId}/boxes': 'put',
        '/v2/campaigns/{campaignId}/orders/{orderId}/status': 'put',
    },
    'yandex_market_notifications': {'/notification': 'post'},
}
DOCUMENTATION = {'description', 'summary', 'example', 'examples', 'externalDocs'}
NAMED_FIELDS = {'properties', 'headers', 'content'}


def contract_fields(node, named_fields=False):
    """
    The node without documentation and x- extensions. Keys of properties, headers and content are names, not
    keywords, and stay.
    """
    if isinstance(node, list):
        return [contract_fields(item) for item in node]
    if isinstance(node, dict):
        return {
            key: contract_fields(value, key in NAMED_FIELDS)
            for key, value in node.items()
            if named_fields or (key not in DOCUMENTATION and not key.startswith('x-'))
        }
    return node


def references(node):
    if isinstance(node, list):
        for value in node:
            yield from references(value)
    elif isinstance(node, dict):
        for key, value in node.items():
            if key == '$ref':
                yield value
            else:
                yield from references(value)


def bundle(spec, operations):
    if not spec['openapi'].startswith('3.0.'):
        raise ValueError(f"Expected OpenAPI 3.0, got {spec['openapi']}")

    paths = {}
    for path, method in operations.items():
        path_item = spec['paths'][path]
        paths[path] = contract_fields({
            **{key: path_item[key] for key in ('parameters', 'servers') if key in path_item},
            method: path_item[method],
        })

    original = spec.get('components', {})
    components = {'securitySchemes': original.get('securitySchemes', {})}
    pending = list(references(paths))
    while pending:
        ref = pending.pop()
        if not ref.startswith('#/components/'):
            raise ValueError(f'Cannot resolve {ref!r} from the local source schema')
        section, name = ref.split('/')[2:4]
        selected = components.setdefault(section, {})
        if name not in selected:
            selected[name] = contract_fields(original[section][name])
            pending.extend(references(selected[name]))

    result = {
        'openapi': spec['openapi'],
        'info': {key: spec['info'][key] for key in ('title', 'version')},
        'paths': paths,
        'components': components,
    }
    for key in ('servers', 'security'):
        if key in spec:
            result[key] = contract_fields(spec[key])
    return result


def normalize_ozon(spec):
    schemas = spec['components']['schemas']
    posting_filter = schemas.get('posting.v4.PostingFbsListRequest.Filter', {})
    for name in ('since', 'to'):
        date_field = posting_filter.get('properties', {}).get(name, {})
        if date_field.get('format') == 'date-time' and date_field.get('pattern') == ' YYYY-MM-DDThh:mm:ssZ':
            # This literal format example cannot match any RFC 3339 timestamp.
            del date_field['pattern']

    stock = schemas.get('productv2ProductsStocksRequestStock', {})
    properties = stock.get('properties', {})
    if stock.get('required') == ['product_id', 'quant_size', 'stock', 'warehouse_id'] and 'quant_size' not in properties:
        # The operation documents either product identifier. The example omits quant_size.
        stock['required'] = ['stock', 'warehouse_id']
        stock['anyOf'] = [{'required': ['offer_id']}, {'required': ['product_id']}]


def bundle_yandex_market(source, operations):
    root = yaml.safe_load((source / 'openapi.yaml').read_text(encoding='utf-8'))
    components = {}
    if 'components' in root:
        components['securitySchemes'] = {'ApiKey': root['components']['securitySchemes']['ApiKey']}

    def component_ref(ref, directory):
        target = (directory / ref).resolve()
        section, filename = target.relative_to(source / 'components').parts
        component = Path(filename).stem
        definitions = components.setdefault(section, {})
        if component not in definitions:
            definitions[component] = None
            definition = yaml.safe_load(target.read_text(encoding='utf-8'))
            definitions[component] = rewrite(definition, target.parent)
        return f'#/components/{section}/{component}'

    # Keep references local to the bundle, including cycles such as the region's parent.
    def rewrite(value, directory):
        if isinstance(value, list):
            return [rewrite(item, directory) for item in value]
        if not isinstance(value, dict):
            return value
        if '$ref' in value:
            return {**value, '$ref': component_ref(value['$ref'], directory)}
        if 'propertyName' in value and 'mapping' in value:
            return {**value, 'mapping': {name: component_ref(ref, directory) for name, ref in value['mapping'].items()}}
        return {key: rewrite(item, directory) for key, item in value.items()}

    paths = {}
    for url, method in operations.items():
        path = source / root['paths'][url]['$ref']
        operation = yaml.safe_load(path.read_text(encoding='utf-8'))[method]
        paths[url] = {method: rewrite(operation, path.parent)}
    result = {
        'openapi': root['openapi'],
        'info': root['info'],
        'paths': paths,
        'components': components,
    }
    if 'servers' in root:
        result['servers'] = root['servers']
    if 'securitySchemes' in components:
        result['security'] = [{'ApiKey': []}]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('marketplace', choices=(*SOURCES, *YANDEX_OPERATIONS))
    parser.add_argument('source', type=Path, help='Local schema file or a checkout of the Yandex Market API repository')
    parser.add_argument('--source-url', help='Actual download URL if the source came from a mirror')
    args = parser.parse_args()
    destination = Path(__file__).with_name(f'{args.marketplace}.json')
    if args.marketplace in YANDEX_OPERATIONS:
        checkout = args.source.resolve()
        revision = check_output(['git', '-C', checkout, 'rev-parse', 'HEAD'], text=True).strip()
        if check_output(['git', '-C', checkout, 'status', '--porcelain', '--', 'openapi', 'LICENSE'], text=True):
            parser.error('The upstream checkout must have a clean spec and license')
        result = bundle_yandex_market(checkout / 'openapi', YANDEX_OPERATIONS[args.marketplace])
        result['x-upstream-commit'] = revision
        copyfile(checkout / 'LICENSE', destination.with_suffix('.LICENSE'))
    else:
        url, operations = SOURCES[args.marketplace]
        raw = args.source.read_bytes()
        source = json.loads(raw) if args.source.suffix == '.json' else yaml.safe_load(raw)
        result = bundle(source, operations)
        if args.marketplace == 'ozon':
            normalize_ozon(result)
        result['x-source-url'] = args.source_url or url
        if args.source_url and args.source_url != url:
            result['x-upstream-url'] = url
        result['x-source-sha256'] = hashlib.sha256(raw).hexdigest()
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
