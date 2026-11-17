"""
Revalidation of the storefronts' static pages. A storefront tags each request its pages make to the API with the
data it asks for (see lib/queries in the storefronts), e.g. the products right in a category with category:<id>.
A change here is turned into the tags of the data it touches and sent to the storefronts of the sites it is on;
each storefront renders the pages that used those tags again.

Tags, keep them in step with the storefronts' lib/queries:

    catalog                 the category tree, in the menu of every page
    category:<id>           the products right in the category, the adverts of the category
    category-path:<path>    the category itself, by its path from the site's root, e.g. sewing/machines
    category-tree:<id>      the products in the category and in its subcategories
    firstpage               the products of the home page
    product:<code>          the product
    actions                 the list of sales actions
    action:<slug>           the sales action and its products
    adverts:<place>         the adverts of a place
    stores, store:<id>      the list of stores, a store
    servicecenters          the list of service centers
    pages, page:<url>       the list of pages, a page by its url, e.g. /about/
    news                    the news
    reviews                 the reviews
    site                    the site's profile

Changes are collected while the transaction lasts and sent once it commits, a batch of tags per site through the
revalidate_nextjs task: the admin saves an object and then its many-to-many relations, each with signals of its
own, and the storefronts must read the data back after it is committed. Outside a transaction they are sent at once,
so a task that changes many products collects them and calls revalidate_products() once.

A batch expires the tags at once, so that the next visit renders the page, or in the background (stale-while-
revalidate), so that the next visit gets the page as it was and starts rendering it. Edits and new prices expire at
once; stock that only changed in the background.
"""
import logging

from collections import defaultdict

from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models import QuerySet

from sewingworld.tasks import PRIORITY_IDLE

logger = logging.getLogger('shop')

TAGS_PER_REQUEST = 500

# fields of a category that the tree shows, see CategoryTreeSerializer; a change of any of them changes the menu
CATEGORY_TREE_FIELDS = ('name', 'subname', 'slug', 'parent_id', 'active', 'hidden', 'feed', 'svg_icon', 'image')


def product_tag(code):
    return f'product:{code}'


def category_listing_tags(category_ids):
    """ The lists of products in the categories: right in each of them, and in each of them or its ancestors """
    from shop.models import Category

    category_ids = set(category_ids)
    if not category_ids:
        return set()
    categories = Category.objects.filter(pk__in=category_ids)
    ancestors = Category.objects.get_queryset_ancestors(categories, include_self=True).values_list('pk', flat=True)
    return {f'category:{pk}' for pk in category_ids} | {f'category-tree:{pk}' for pk in ancestors}


def category_sites(category):
    """ Sites whose catalog has the category: their root category is the root of its tree """
    from sewingworld.models import SiteProfile

    profiles = SiteProfile.objects.filter(revalidation_token__gt='').select_related('root_category')
    return [profile.site_id for profile in profiles
            if profile.root_category is None or profile.root_category.tree_id == category.tree_id]


def stock_state(num, pack_factor=1, ws_pack_only=False):
    """
    What the storefronts show of the stock: out of stock, the last one, in stock, more than five (a choice of
    quantity), and for products sold in whole packs, whether a pack is in stock. Other changes of stock show nowhere.
    """
    return (num <= 0, num == 1, num > 5, bool(ws_pack_only) and num >= pack_factor)


def resolve_sites(sites):
    """ Ids of the sites: None for every site, ids, Sites, or a queryset of Sites """
    if sites is None:
        return None
    if isinstance(sites, QuerySet):
        return set(sites.values_list('pk', flat=True))
    return {site.pk if isinstance(site, Site) else site for site in sites}


class Batch:
    """ Changes of a transaction """

    def __init__(self):
        # (site ids now or None for every site, queryset of more sites read again at commit, background) -> tags
        self.tags = defaultdict(set)
        # background -> product ids, whose pages and lists are worked out at commit
        self.products = {False: set(), True: set()}
        # product id -> tags of its sites and sites it has left
        self.product_tags = defaultdict(set)
        self.product_sites = defaultdict(set)
        # products whose page only shows another product, such as an accessory
        self.product_pages = set()
        # product id -> stock it had, None if it was not counted
        self.stock = {}
        self.flushed = False

    def flush(self):
        if self.flushed:
            return
        self.flushed = True
        sites = {site.pk: site for site in Site.objects.filter(profile__revalidation_token__gt='').select_related('profile')}
        if not sites:
            return
        per_site = {pk: {False: set(), True: set()} for pk in sites}

        def add(site_ids, tags, background):
            for pk in sites if site_ids is None else site_ids:
                if pk in per_site:
                    per_site[pk][background] |= tags

        for (site_ids, queryset, background), tags in self.tags.items():
            if queryset is not None:
                site_ids = set(site_ids) | resolve_sites(queryset)
            add(site_ids, tags, background)

        self.check_stock()
        for background in (False, True):
            for product_sites, tags in expand_products(self.products[background], self.product_tags, self.product_sites):
                add(product_sites, tags, background)
        for product_sites, tags in expand_product_pages(self.product_pages):
            add(product_sites, tags, False)

        from shop.tasks.workflow import revalidate_nextjs

        for pk, tags in per_site.items():
            site = sites[pk]
            for background, chunk in [(False, sorted(tags[False]))] + [(True, sorted(tags[True] - tags[False]))]:
                for start in range(0, len(chunk), TAGS_PER_REQUEST):
                    payload = {'tags': chunk[start:start + TAGS_PER_REQUEST]}
                    if background:
                        payload['background'] = True
                    revalidate_nextjs.s(site.domain, site.profile.revalidation_token, payload).apply_async(priority=PRIORITY_IDLE)

    def check_stock(self):
        """ Counts the stock of the products again and takes those whose stock shows otherwise """
        from shop.models import Product

        if not self.stock:
            return
        for product in Product.objects.filter(pk__in=self.stock).only('num', 'pack_factor', 'ws_pack_only'):
            previous = self.stock[product.pk]
            current = stock_state(product.instock, product.pack_factor, product.ws_pack_only)  # counts it if reset
            if previous is None or stock_state(previous, product.pack_factor, product.ws_pack_only) != current:
                if product.pk not in self.products[False]:
                    self.products[True].add(product.pk)


def current_batch():
    """
    The batch of the transaction, sent once it commits. Its callback leaves the connection's list when it runs and
    when the transaction, or the savepoint it was added in, rolls back: then the next change starts a new batch.
    """
    connection = transaction.get_connection()
    if not connection.in_atomic_block:
        return None
    batch = getattr(connection, 'revalidation_batch', None)
    if batch is None or batch.flushed or not any(func == batch.flush for _, func, *_ in connection.run_on_commit):
        batch = Batch()
        connection.revalidation_batch = batch
        # robust: once the transaction has committed, a failure here, such as the broker down, is only logged
        transaction.on_commit(batch.flush, robust=True)
    return batch


def collect(add):
    """ Adds a change to the transaction's batch, or sends it at once outside a transaction """
    batch = current_batch()
    if batch is None:
        batch = Batch()
        add(batch)
        try:
            batch.flush()
        except Exception:
            # the change is saved already, the pages are rendered again after a while anyway
            logger.exception('Revalidation failed')
    else:
        add(batch)


def revalidate(tags, sites=None, background=False):
    """
    The tags on the sites: None for every site, ids or Sites, or a queryset of Sites. A queryset is read now and once
    more at commit, as the admin saves the sites of an object after the object: both those it had and those it has
    get the tags, so a storefront that it leaves renders its pages too.
    """
    tags = set(tags)
    if not tags:
        return
    queryset = sites if isinstance(sites, QuerySet) else None
    site_ids = resolve_sites(sites)
    key = (None if site_ids is None else frozenset(site_ids), queryset, background)
    collect(lambda batch: batch.tags[key].update(tags))


def revalidate_products(products, background=False, tags=(), sites=()):
    """
    The pages that show the products: their own, the lists of their categories, sales actions and the home page, and
    the pages of products that show them, on the sites the products are on. tags are more tags of the products, such
    as a category they have left; sites are more sites, those they have left.
    """
    products = set(products)
    if not products:
        return
    site_ids = resolve_sites(sites)

    def add(batch):
        if background:
            batch.products[True].update(products - batch.products[False])
        else:
            batch.products[False].update(products)
            batch.products[True] -= products
        for pk in products:
            batch.product_tags[pk].update(tags)
            batch.product_sites[pk].update(site_ids)
    collect(add)


def revalidate_product_pages(products):
    """ The products' own pages only, for what only they show, such as the manufacturer """
    products = set(products)
    if products:
        collect(lambda batch: batch.product_pages.update(products))


def revalidate_stock(stock):
    """
    The products whose stock changed: {id: stock before, None if not counted}. The stock is counted again at commit,
    and products whose stock shows otherwise are revalidated in the background.
    """
    def add(batch):
        for pk, num in stock.items():
            batch.stock.setdefault(pk, None if num is None or num < 0 else num)
    if stock:
        collect(add)


def expand_products(products, extra_tags=None, extra_sites=None):
    """ (site ids, tags) of each product, the sets that include them taken as changed too """
    from shop.models import Category, Product, ProductRelation, ProductSet

    if not products:
        return []
    extra_tags = extra_tags or {}
    extra_sites = extra_sites or {}
    # a set costs the sum of its parts, and is in stock when they are
    declarations = set(ProductSet.objects.filter(constituent__in=products).values_list('declaration_id', flat=True))
    products = set(products) | declarations

    rows = Product.objects.filter(pk__in=products).values_list('pk', 'code', 'firstpage')
    tags = {pk: {product_tag(code)} | ({'firstpage'} if firstpage else set()) for pk, code, firstpage in rows}
    for pk in products:
        tags.setdefault(pk, set()).update(extra_tags.get(pk, ()))

    sites = defaultdict(set)
    for pk, site in Product.sites.through.objects.filter(product_id__in=products).values_list('product_id', 'site_id'):
        sites[pk].add(site)
    for pk in products:
        sites[pk].update(extra_sites.get(pk, ()))

    in_categories = defaultdict(set)
    for pk, category in Product.categories.through.objects.filter(product_id__in=products).values_list('product_id', 'category_id'):
        in_categories[pk].add(category)
    categories = {category for ids in in_categories.values() for category in ids}
    if categories:
        nodes = Category.objects.filter(pk__in=categories).values_list('pk', 'tree_id', 'lft', 'rght')
        ancestors = list(Category.objects.get_queryset_ancestors(Category.objects.filter(pk__in=categories), include_self=True)
                         .values_list('pk', 'tree_id', 'lft', 'rght'))
        lineage = {pk: [a for a, a_tree, a_lft, a_rght in ancestors if a_tree == tree and a_lft <= lft and a_rght >= rght]
                   for pk, tree, lft, rght in nodes}
        for pk, ids in in_categories.items():
            tags[pk].update(f'category:{category}' for category in ids)
            tags[pk].update(f'category-tree:{ancestor}' for category in ids for ancestor in lineage.get(category, ()))

    for pk, slug in Product.sales_actions.through.objects.filter(product_id__in=products).values_list('product_id', 'salesaction__slug'):
        tags[pk].add(f'action:{slug}')

    # products that show them: as accessories, similar products or gifts
    parents = set(ProductRelation.objects.filter(child_product__in=products).values_list('parent_product_id', flat=True))
    return [(sites[pk], tags[pk]) for pk in products] + expand_product_pages(parents - products)


def expand_product_pages(products):
    """ (site ids, tags) of each product's own page """
    from shop.models import Product

    if not products:
        return []
    sites = defaultdict(set)
    for pk, site in Product.sites.through.objects.filter(product_id__in=products).values_list('product_id', 'site_id'):
        sites[pk].add(site)
    return [(sites[pk], {product_tag(code)}) for pk, code in Product.objects.filter(pk__in=products).values_list('pk', 'code')]
