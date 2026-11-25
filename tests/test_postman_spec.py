import json
import re
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import SimpleTestCase

from sewingworld.management.commands.postman_spec import NOT_ALLOWED, SIDE_EFFECTS

TEST_SCRIPT = Path(__file__).resolve().parent.parent / 'postman' / 'test.js'


class PostmanSpecTests(SimpleTestCase):
    """ The spec of the Postman collection still fits the API, see postman/README.md """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        out = StringIO()
        with redirect_stderr(StringIO()):  # drf-spectacular prints its warnings about the schema there
            call_command('postman_spec', stdout=out)  # fails on a path parameter without a variable
        cls.spec = json.loads(out.getvalue())

    def operations(self):
        for path, item in self.spec['paths'].items():
            for method, operation in item.items():
                if method in ('get', 'put', 'post', 'patch', 'delete'):
                    yield method, path, operation

    def test_path_parameters_are_collection_variables(self):
        for method, path, operation in self.operations():
            for parameter in operation.get('parameters', []):
                # template_name takes a document name, such as bill, rather than a variable
                if parameter['in'] == 'path' and parameter['name'] != 'template_name':
                    self.assertRegex(parameter['example'], r'^\{\{\w+\}\}$', '%s %s' % (method, path))

    def test_only_side_effects_are_marked(self):
        marked = {(method, operation['summary']) for method, _, operation in self.operations()
                  if operation['summary'].startswith('⚠')}
        self.assertEqual(marked, {(method, '⚠ ' + path.lstrip('/')) for method, path in SIDE_EFFECTS})

    def test_names_are_unique_per_method(self):
        names = [(method, operation['summary']) for method, _, operation in self.operations()]
        self.assertEqual(len(names), len(set(names)))

    def test_endpoints_outside_api_go_to_storefront(self):
        for path, item in self.spec['paths'].items():
            if not path.startswith('/api/'):
                self.assertEqual(item['servers'][0]['url'], '{origin}', path)

    def test_script_knows_operations_without_methods(self):
        """ test.js expects 405 from the same operations as the command """
        script = TEST_SCRIPT.read_text()
        listed = re.search(r'const NOT_ALLOWED = \[(.*?)\];', script, re.S).group(1)
        self.assertEqual(set(re.findall(r"'(\w+) ([^']+)'", listed)),
                         {(method.upper(), path.lstrip('/')) for method, path in NOT_ALLOWED})
