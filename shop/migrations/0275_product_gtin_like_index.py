"""
The LIKE index of shop_product.gtin, which Django makes for a CharField with db_index and production lacks: the field
got its index in a way that left it out. A database made from the squashed migration has it, and this migration leaves
it alone.

The index is built CONCURRENTLY, not to block writes to the products, so the migration isn't atomic. A build that fails
leaves an invalid index, which migrating again drops and builds anew.
"""
from django.db import migrations

TABLE = 'shop_product'
INDEX = 'shop_product_gtin_6cfef463_like'  # the name Django gives it


def add_like_index(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    quote = schema_editor.quote_name
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            'SELECT i.indisvalid FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid '
            'WHERE c.relname = %s AND c.relnamespace = current_schema()::regnamespace',
            [INDEX],
        )
        row = cursor.fetchone()
    if row is not None and row[0]:
        return
    if row is not None:
        schema_editor.execute(f'DROP INDEX CONCURRENTLY {quote(INDEX)}')
    schema_editor.execute(f'CREATE INDEX CONCURRENTLY {quote(INDEX)} ON {quote(TABLE)} ("gtin" varchar_pattern_ops)')


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('shop', '0001_squashed_0274_integration_check'),
    ]

    operations = [
        migrations.RunPython(add_like_index, migrations.RunPython.noop, elidable=True),
    ]
