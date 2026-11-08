"""
Converts the Bootstrap (3 to 5) and Cartzilla classes in the HTML stored in the database to Tailwind CSS classes.

The storefronts render this HTML as it is. Tailwind only generates the classes it finds in a frontend's sources, so
every frontend imports the same `src/backend-safelist.css`, printed by `manage.py tailwindize_html --safelist`.
Editors may use only the classes listed there; anything else renders unstyled.

Only the class attributes of the affected start tags are rewritten in place, the rest of the HTML stays byte-identical
(the admin forms tidy it). Tags inside <svg> are never touched, their classes belong to the SVG's own styles.

How classes are converted:
- `row` becomes a 12-column grid without negative margins. Rows of the old 24-column grid (a md span of 8, 10 or 12, or
  any span above 12) get their spans halved and rounded up: 10+14 becomes 5+7, a lone `col-md-15` becomes 8.
  Columns of equal width become `grid-cols-N` on the row with no classes on the columns, others get `col-span-N`.
  `col-*` outside a row is dropped.
- `ratio ratio-16x9` and Bootstrap 4's `embed-responsive embed-responsive-16by9` become `aspect-video` (4x3 and 4by3
  become `aspect-4/3`), their child elements fill them with `size-full`.
- Utilities get their Tailwind names with Cartzilla's spacers (3, 4 and 5 become 4, 6 and 12) and Tailwind's
  breakpoint prefixes; `card`, `btn` and a few other components become short utility lists. Bootstrap's utilities were
  !important: on elements the typography plugin styles (headings, paragraphs, lists, links...) the classes of
  margins, paddings, font sizes, weights and colors get Tailwind's ! suffix, so they still win over `prose`.
- Kept as they are: the site's `sw-file-*` link icons, the hooks of embedded scripts (`ya-*`, `yd-*`) and the classes
  that a <style> element in the same HTML styles (some pages bring their own styles).
- Everything else is dropped: classes of Bootstrap 3, Font Awesome, WordPress and the old site that have no styles any
  more. The command's report lists every dropped class.

End of the migration, in this order:
1. Convert janome.club to Tailwind, with the safelist (singer, familysew, dor-tak and cartzilla have it already).
2. Regenerate the safelist with `--safelist` and copy it to every frontend if it changed, deploy all frontends.
3. Run `manage.py tailwindize_html --write` in production. In the same deploy, drop the `img-fluid` class that
   `ProductSerializer.get_stitches` adds to the stitches picture. Pages show the new HTML once their cache expires
   (an hour) or after a redeploy.
4. In every frontend, delete `src/backend-content.css` and the `backend-content` class: cartzilla's `contentClass` in
   `components/ui/content.ts` already has the typography (`prose`). singer, familysew and dor-tak move their
   typography to `prose` too, keep their `sw-file-*` rules in `styles.css` and drop the `rebootstrap()` helpers of
   their product pages.
5. From then on, editors use only the safelisted classes; `--check path/to/backend-safelist.css` lists any others found in the database.
"""
import math
import re
from collections import Counter, defaultdict

from bs4 import BeautifulSoup, Tag

# Fields with HTML that the storefronts render, as app_label.Model: [fields].
# Category.svg_icon is not here: its classes belong to the SVG's own styles.
FIELDS = {
    'shop.Product': ['descr', 'spec', 'manuals', 'stitches', 'complect', 'dealertxt', 'shortdescr', 'state'],
    'shop.SalesAction': ['brief', 'description'],
    'shop.Category': ['brief', 'description'],
    'shop.Advert': ['content'],
    'shop.Store': ['description'],
    'shop.News': ['content'],
    'flatpages.FlatPage': ['content'],
    'blog.Entry': ['content'],
}

# Bootstrap's breakpoint infixes and Tailwind's prefixes for them
BREAKPOINTS = ['', 'sm', 'md', 'lg', 'xl', 'xxl']
PREFIXES = {'': '', 'sm': 'sm:', 'md': 'md:', 'lg': 'lg:', 'xl': 'xl:', 'xxl': '2xl:'}

# Cartzilla's spacers (0.25, 0.5, 1, 1.5 and 3rem) in Tailwind's spacing scale
SPACERS = {'0': '0', '1': '1', '2': '2', '3': '4', '4': '6', '5': '12', 'auto': 'auto'}
SPACING_PROPERTIES = {
    'm': 'm', 'mt': 'mt', 'mb': 'mb', 'ms': 'ms', 'me': 'me', 'mx': 'mx', 'my': 'my', 'ml': 'ms', 'mr': 'me',
    'p': 'p', 'pt': 'pt', 'pb': 'pb', 'ps': 'ps', 'pe': 'pe', 'px': 'px', 'py': 'py', 'pl': 'ps', 'pr': 'pe',
}
DISPLAYS = {
    'none': 'hidden', 'inline': 'inline', 'inline-block': 'inline-block', 'block': 'block', 'flex': 'flex',
    'inline-flex': 'inline-flex', 'grid': 'grid', 'table': 'table', 'table-cell': 'table-cell', 'table-row': 'table-row',
}
TEXT_ALIGNS = {'left': 'left', 'start': 'start', 'center': 'center', 'right': 'right', 'end': 'end'}
JUSTIFY = {'start': 'start', 'end': 'end', 'center': 'center', 'between': 'between', 'around': 'around', 'evenly': 'evenly'}
ALIGN_ITEMS = {'start': 'start', 'end': 'end', 'center': 'center', 'baseline': 'baseline', 'stretch': 'stretch'}

# Classes that keep their name and meaning in Tailwind, or are the site's own
SAME = {
    'relative', 'absolute', 'fixed', 'static', 'sticky', 'overflow-hidden', 'overflow-auto', 'invisible', 'sr-only',
    'text-primary', 'text-accent', 'text-success', 'text-info', 'text-warning', 'text-danger', 'text-dark',
    'text-white', 'text-muted', 'bg-white', 'bg-dark', 'bg-primary', 'bg-accent', 'bg-success', 'bg-info',
    'bg-warning', 'bg-danger', 'bg-transparent', 'border', 'border-0', 'mx-auto', 'opacity-50', 'opacity-75',
    'shadow', 'shadow-sm', 'shadow-lg', 'top-0', 'bottom-0', 'start-0', 'end-0',
    'sw-file-pdf', 'sw-file-video', 'sw-file-web', 'container',
}
# Script hooks of embedded widgets (Yandex site search, Yandex delivery)
KEEP_PREFIXES = ('ya-', 'yd-')

# Bootstrap and Cartzilla classes with a Tailwind equivalent
SIMPLE = {
    'text-light': 'text-white',
    'bg-light': 'bg-white',
    'bg-secondary': 'bg-gray-100',
    'text-uppercase': 'uppercase',
    'text-lowercase': 'lowercase',
    'text-capitalize': 'capitalize',
    'text-nowrap': 'whitespace-nowrap',
    'text-truncate': 'truncate',
    'fw-bold': 'font-bold',
    'fw-bolder': 'font-bold',
    'fw-medium': 'font-medium',
    'fw-semibold': 'font-semibold',
    'fw-normal': 'font-normal',
    'fw-light': 'font-light',
    'fst-italic': 'italic',
    'small': 'text-sm',
    'fs-xs': 'text-xs',
    'fs-ms': 'text-sm',
    'fs-sm': 'text-sm',
    'fs-md': 'text-base',
    'fs-base': 'text-base',
    'fs-lg': 'text-lg',
    'fs-xl': 'text-2xl',
    'fs-6': 'text-base',
    'fs-5': 'text-xl',
    'fs-4': 'text-2xl',
    'fs-3': 'text-3xl',
    'lead': 'text-lg font-light',
    'h1': 'text-4xl font-medium',
    'h2': 'text-3xl font-medium',
    'h3': 'text-2xl font-medium',
    'h4': 'text-xl font-medium',
    'h5': 'text-lg font-medium',
    'h6': 'text-base font-medium',
    'w-100': 'w-full',
    'w-75': 'w-3/4',
    'w-50': 'w-1/2',
    'w-25': 'w-1/4',
    'h-100': 'h-full',
    'mw-100': 'max-w-full',
    'mh-100': 'max-h-full',
    'position-relative': 'relative',
    'position-absolute': 'absolute',
    'position-fixed': 'fixed',
    'position-static': 'static',
    'position-sticky': 'sticky',
    'flex-row': 'flex-row',
    'flex-column': 'flex-col',
    'flex-wrap': 'flex-wrap',
    'flex-nowrap': 'flex-nowrap',
    'flex-fill': 'flex-1',
    'flex-grow-1': 'grow',
    'flex-shrink-0': 'shrink-0',
    'border-top': 'border-t',
    'border-bottom': 'border-b',
    'border-start': 'border-s',
    'border-end': 'border-e',
    'rounded': 'rounded-md',
    'rounded-0': 'rounded-none',
    'rounded-3': 'rounded-lg',
    'rounded-circle': 'rounded-full',
    'rounded-pill': 'rounded-full',
    'float-start': 'float-left',
    'float-left': 'float-left',
    'pull-left': 'float-left',
    'float-end': 'float-right',
    'float-right': 'float-right',
    'pull-right': 'float-right',
    'visually-hidden': 'sr-only',
    'lh-1': 'leading-none',
    'opacity-60': 'opacity-60',
    'opacity-70': 'opacity-70',
    'img-thumbnail': 'rounded-md border bg-white p-1',
    'aligncenter': 'mx-auto',
    'container-fluid': 'w-full',
    'list-unstyled': 'list-none ps-0',
    # Bootstrap's card, a bordered white box, and its padded body
    'card': 'relative flex min-w-0 flex-col rounded-lg border bg-white',
    'card-body': 'flex-auto p-5',
    # Cartzilla's product card texts, pasted into store descriptions
    'product-title': 'text-sm font-medium',
    'product-meta': 'text-xs text-muted',
    # Bootstrap 5's caption over a carousel picture
    'carousel-caption': 'absolute inset-x-[15%] bottom-5 py-5 text-center text-white',
    'display-1': 'text-7xl font-medium leading-none',
    'display-2': 'text-7xl font-medium leading-none',
    'display-3': 'text-6xl font-medium leading-none',
    'display-4': 'text-6xl font-medium leading-none',
    'display-5': 'text-5xl font-medium leading-none',
    'display-6': 'text-4xl font-medium leading-none',
    # Bootstrap 5.3 names, used by pages written for it
    'object-fit-cover': 'object-cover',
    'object-fit-contain': 'object-contain',
    'bg-body-tertiary': 'bg-gray-100',
    'badge': 'inline-block rounded-md px-2 py-1 text-xs leading-none font-medium whitespace-nowrap',
}

# Buttons: a base, a color and a size. `btn` alone is a plain button with a border.
BUTTON_BASE = 'inline-block rounded-md border text-center align-middle no-underline'
BUTTON_VARIANTS = {
    'btn-primary': 'border-primary bg-primary text-white hover:bg-primary-hover',
    'btn-accent': 'border-accent bg-accent text-white hover:bg-accent-hover',
    'btn-success': 'border-success bg-success text-white hover:bg-success-hover',
    'btn-danger': 'border-danger bg-danger text-white',
    'btn-info': 'border-info bg-info text-white',
    'btn-warning': 'border-warning bg-warning text-white',
    'btn-dark': 'border-dark bg-dark text-white',
    'btn-secondary': 'border-gray-200 bg-gray-200 text-gray-700',
    'btn-outline-primary': 'border-primary text-primary hover:bg-primary hover:text-white',
    'btn-default': 'border-gray-300 bg-white text-gray-700',
}
BUTTON_SIZES = {
    'btn-xs': 'px-2 py-1 text-xs',
    'btn-sm': 'px-4 py-1.5 text-sm',
    '': 'px-5 py-2.5',
    'btn-lg': 'px-6 py-3 text-lg',
}

RATIOS = {
    'ratio-16x9': 'aspect-video', 'embed-responsive-16by9': 'aspect-video',
    'ratio-4x3': 'aspect-4/3', 'embed-responsive-4by3': 'aspect-4/3',
    'ratio-1x1': 'aspect-square', 'embed-responsive-1by1': 'aspect-square',
}
RATIO_CONTAINERS = {'ratio', 'embed-responsive'}

COLUMN = re.compile(r'^col(?:-(sm|md|lg|xl|xxl))?(?:-(\d+|auto))?$')
SPACING = re.compile(r'^(m|mt|mb|ms|me|mx|my|ml|mr|p|pt|pb|ps|pe|px|py|pl|pr)-(?:(sm|md|lg|xl|xxl)-)?(n?)([0-5]|auto)$')
DISPLAY = re.compile(r'^d-(?:(sm|md|lg|xl|xxl)-)?(' + '|'.join(DISPLAYS) + ')$')
TEXT_ALIGN = re.compile(r'^text-(?:(sm|md|lg|xl|xxl)-)?(' + '|'.join(TEXT_ALIGNS) + ')$')
JUSTIFY_CONTENT = re.compile(r'^justify-content-(?:(sm|md|lg|xl|xxl)-)?(' + '|'.join(JUSTIFY) + ')$')
ALIGN = re.compile(r'^align-items-(?:(sm|md|lg|xl|xxl)-)?(' + '|'.join(ALIGN_ITEMS) + ')$')
GAP = re.compile(r'^gap-([0-5])$')


def map_simple(name):
    """The Tailwind classes for one class without context, '' to drop it, None if it is unknown"""
    if name in SAME or name.startswith(KEEP_PREFIXES):
        return name
    if name in SIMPLE:
        return SIMPLE[name]
    if m := SPACING.match(name):
        prop, bp, negative, value = m.groups()
        if negative and value == 'auto':
            return None
        return f"{PREFIXES[bp or '']}{'-' if negative else ''}{SPACING_PROPERTIES[prop]}-{SPACERS[value]}"
    if m := DISPLAY.match(name):
        return PREFIXES[m.group(1) or ''] + DISPLAYS[m.group(2)]
    if m := TEXT_ALIGN.match(name):
        return f"{PREFIXES[m.group(1) or '']}text-{TEXT_ALIGNS[m.group(2)]}"
    if m := JUSTIFY_CONTENT.match(name):
        return f"{PREFIXES[m.group(1) or '']}justify-{JUSTIFY[m.group(2)]}"
    if m := ALIGN.match(name):
        return f"{PREFIXES[m.group(1) or '']}items-{ALIGN_ITEMS[m.group(2)]}"
    if m := GAP.match(name):
        return f'gap-{SPACERS[m.group(1)]}'
    return None


def column_spans(classes):
    """Bootstrap column spans of an element by breakpoint, e.g. {'md': 4}; 'auto' for `col` and `col-md`"""
    spans = {}
    for name in classes:
        if m := COLUMN.match(name):
            bp, span = m.group(1) or '', m.group(2)
            spans[bp] = 'auto' if span is None else span if span == 'auto' else int(span)
    return spans


def is_24_column(children_spans):
    """Rows of the old 24-column grid have a md span of 8, 10 or 12 or any span above 12"""
    for spans in children_spans:
        for bp, span in spans.items():
            if isinstance(span, int) and (span > 12 or (bp != '' and span in (8, 10, 12))):
                return True
    return False


def effective_spans(children_spans, wide):
    """The 12-column span of each child at every breakpoint; a span carries over to larger breakpoints.
    `col` shares what fixed columns leave, `col-auto` is treated as `col`."""
    result = []
    for spans in children_spans:
        if wide:  # the old 24-column spans in the 12-column grid, rounded up
            spans = {bp: math.ceil(span / 2) if isinstance(span, int) else span for bp, span in spans.items()}
        current, row = 12, {}
        for bp in BREAKPOINTS:
            if bp in spans:
                current = spans[bp]
            row[bp] = current
        result.append(row)
    for bp in BREAKPOINTS:
        fixed = [row[bp] for row in result if isinstance(row[bp], int)]
        autos = [row for row in result if not isinstance(row[bp], int)]
        if autos:
            share = max(1, (12 - min(sum(fixed), 12)) // len(autos)) if sum(fixed) < 12 else 12 // len(autos) or 1
            for row in autos:
                row[bp] = share
    return result


def plan_row(children_spans):
    """Tailwind classes for a row and for each of its children"""
    wide = is_24_column(children_spans)
    spans = effective_spans(children_spans, wide)
    row_classes = ['grid', 'gap-x-6']
    child_classes = [[] for _ in spans]
    if not spans:
        return row_classes, child_classes, wide
    uniform = all(len({row[bp] for row in spans}) == 1 and 12 % spans[0][bp] == 0 for bp in BREAKPOINTS)
    if uniform:
        columns = 1
        for bp in BREAKPOINTS:
            count = 12 // spans[0][bp]
            if count != columns:
                row_classes.append(f'{PREFIXES[bp]}grid-cols-{count}')
                columns = count
        return row_classes, child_classes, wide
    # columns of different widths: a 12-column grid from the first breakpoint where a child is narrower
    first = next(bp for bp in BREAKPOINTS if any(row[bp] != 12 for row in spans))
    row_classes.append(f'{PREFIXES[first]}grid-cols-12')
    for row, classes in zip(spans, child_classes):
        previous = None
        for bp in BREAKPOINTS[BREAKPOINTS.index(first):]:
            if row[bp] != previous:
                classes.append(f'{PREFIXES[bp]}col-span-{row[bp]}')
                previous = row[bp]
    return row_classes, child_classes, wide


def element_children(tag):
    return [child for child in tag.children if isinstance(child, Tag)]


def in_svg(tag):
    return tag.name == 'svg' or any(parent.name == 'svg' for parent in tag.parents)


# Classes only the conversion (or an editor after it) writes, never Bootstrap: a value with one of them is converted
CONVERTED = re.compile(r'^(?:[a-z0-9]+:.+|.+!|.*\[.+\]|inset-.+|grid|flex-col|grow|w-full|h-full|max-w-full|whitespace-nowrap|truncate'
                       r'|(?:font|aspect|col-span|grid-cols|gap-x)-.+|items-(?:start|end|center|baseline|stretch)'
                       r'|justify-(?:start|end|center|between|around|evenly)|rounded-(?:md|lg|full|none)'
                       r'|text-(?:xs|sm|base|lg|xl|[234]xl))$')


class Report:
    def __init__(self):
        self.mapped = Counter()   # (old, new) -> count
        self.dropped = Counter()  # old -> count
        self.kept = Counter()     # old -> count
        self.emitted = Counter()  # new class -> count
        self.rows = Counter()     # '12' or '24' -> count of rows
        self.converted = 0        # values skipped because they are converted already

    def update(self, other):
        for name in ('mapped', 'dropped', 'kept', 'emitted', 'rows'):
            getattr(self, name).update(getattr(other, name))
        self.converted += other.converted


# Elements that the frontends' typography (Tailwind's `prose`) styles, and the classes that set what it sets on them.
# Bootstrap's utilities were !important, so on these elements such classes get Tailwind's ! to keep winning.
# Bootstrap components, their classes aren't !important (unlike Bootstrap's utilities)
COMPONENTS = {'card', 'card-body', 'product-title', 'product-meta', 'carousel-caption', 'badge', 'img-thumbnail',
              'container-fluid', 'list-unstyled', 'aligncenter'}
PROSE_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'strong', 'b', 'em', 'img', 'table', 'thead',
              'tbody', 'tr', 'th', 'td', 'blockquote', 'figure', 'figcaption', 'hr', 'dl', 'dt', 'dd'}
# prose sets vertical margins only, and paddings
PROSE_PROPERTIES = re.compile(r'^(?:[a-z0-9]+:)*-?(?:m[tby]?|p[trblxyse]?)-|^(?:[a-z0-9]+:)*(?:text-(?:xs|sm|base|lg|xl|[2-9]xl|muted|dark|'
                              r'primary|accent|success|info|danger|warning|white|gray-\d+)|font-|leading-|uppercase$|list-)')


def convert_classes(tag, plans, styled, report):
    """The new class list of a tag, or None to leave it unchanged. `styled` are classes the HTML's own <style> uses."""
    classes = tag.get('class') or []
    parent = tag.parent if isinstance(tag.parent, Tag) else None
    parent_classes = (parent.get('class') or []) if parent is not None else []
    in_row = parent is not None and 'row' in parent_classes and id(parent) in plans
    in_ratio = parent is not None and bool(RATIO_CONTAINERS & set(parent_classes))
    if not classes and not in_row and not in_ratio:
        return None

    out = []
    utilities = set()  # classes that come from Bootstrap's utilities, which are !important

    def add(names, old=None):
        for name in names.split() if isinstance(names, str) else names:
            if name and name not in out:
                out.append(name)
                report.emitted[name] += 1
        if old is not None:
            report.mapped[(old, names if isinstance(names, str) else ' '.join(names))] += 1

    if 'row' in classes:
        row_classes, _, wide = plans[id(tag)]
        add(row_classes, 'row')
        report.rows['24' if wide else '12'] += 1
    if in_row:
        _, child_classes, _ = plans[id(parent)]
        index = next(i for i, child in enumerate(element_children(parent)) if child is tag)
        add(child_classes[index])
    if in_ratio:
        add('size-full')

    buttons = [name for name in classes if name == 'btn' or name in BUTTON_VARIANTS or name in BUTTON_SIZES]
    if 'btn' in classes:
        variant = next((BUTTON_VARIANTS[name] for name in classes if name in BUTTON_VARIANTS), 'border-gray-300 bg-white')
        size = next((BUTTON_SIZES[name] for name in classes if name in BUTTON_SIZES and name), BUTTON_SIZES[''])
        add(f'{BUTTON_BASE} {variant} {size}', ' '.join(buttons))

    for name in classes:
        if name == 'row' or name in buttons:
            if name in buttons and 'btn' not in classes:
                report.dropped[name] += 1
            continue
        if COLUMN.match(name):
            if not in_row:
                report.dropped[name] += 1
            else:
                report.mapped[(name, '(row grid)')] += 1
            continue
        if name in RATIO_CONTAINERS:
            report.mapped[(name, '(aspect ratio)')] += 1
            continue
        if name in RATIOS:
            add(RATIOS[name], name)
            continue
        if name == 'embed-responsive-item' and in_ratio:
            report.mapped[(name, 'size-full')] += 1
            continue
        if name in styled:  # the page's own class, not Tailwind's
            if name not in out:
                out.append(name)
            report.kept[name] += 1
            continue
        mapped = map_simple(name)
        if name == 'card' and 'product-card' in classes:  # Cartzilla's product card has no border
            mapped = mapped.replace(' border ', ' ')
        if mapped is None:
            report.dropped[name] += 1
            continue
        if mapped == name:
            add(name)
            report.kept[name] += 1
        else:
            add(mapped, name)
        if name not in COMPONENTS:
            utilities.update(mapped.split())
    if tag.name in PROSE_TAGS:
        important = [name + '!' if name in utilities and PROSE_PROPERTIES.match(name) else name for name in out]
        for old, new in zip(out, important):
            if old != new:
                report.emitted[old] -= 1
                if report.emitted[old] <= 0:
                    del report.emitted[old]
                report.emitted[new] += 1
        out = important
    return out


def start_tag_span(html, start):
    """The end offset of the start tag that begins at `start`, quotes respected"""
    quote = None
    for i in range(start + 1, len(html)):
        c = html[i]
        if quote:
            if c == quote:
                quote = None
        elif c in '"\'':
            quote = c
        elif c == '>':
            return i + 1
    return len(html)


CLASS_ATTRIBUTE = re.compile(r'''\s+class\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+)''', re.IGNORECASE)


def rewrite_start_tag(text, classes):
    """The start tag with its class attribute replaced, removed when `classes` is empty, or added"""
    value = ' '.join(classes)
    if CLASS_ATTRIBUTE.search(text):
        if value:
            return CLASS_ATTRIBUTE.sub(lambda m: f' class="{value}"', text, count=1)
        return CLASS_ATTRIBUTE.sub('', text, count=1)
    if not value:
        return text
    end = len(text) - 2 if text.endswith('/>') else len(text) - 1
    while end > 0 and text[end - 1].isspace():
        end -= 1
    return f'{text[:end]} class="{value}"{text[end:]}'


def convert(html):
    """The converted HTML and a report of what changed"""
    report = Report()
    if not html or 'class' not in html:
        return html, report
    soup = BeautifulSoup(html, 'html.parser')
    tags = [tag for tag in soup.find_all(True) if not in_svg(tag)]
    # converting twice would map Tailwind's mb-4 as Bootstrap's and drop the grid
    if any(CONVERTED.match(name) for tag in tags for name in tag.get('class') or []):
        report.converted = 1
        return html, report

    styled = styled_classes(soup)

    plans = {}
    for tag in tags:
        if 'row' in (tag.get('class') or []):
            plans[id(tag)] = plan_row([column_spans(child.get('class') or []) for child in element_children(tag)])

    line_starts = [0] + [m.end() for m in re.finditer('\n', html)]
    edits = []
    for tag in tags:
        new = convert_classes(tag, plans, styled, report)
        if new is None or new == (tag.get('class') or []):
            continue
        if tag.sourceline is None:
            continue
        start = line_starts[tag.sourceline - 1] + tag.sourcepos
        if html[start] != '<':
            raise ValueError(f'No start tag at line {tag.sourceline}, column {tag.sourcepos}')
        end = start_tag_span(html, start)
        edits.append((start, end, rewrite_start_tag(html[start:end], new)))

    for start, end, text in sorted(edits, reverse=True):
        html = html[:start] + text + html[end:]
    return html, report


# Classes editors may use beyond those in the converted database, so a new text can use the same layouts
EDITOR_VOCABULARY = [
    'grid', 'gap-x-6', 'gap-y-4', 'aspect-video', 'aspect-4/3', 'aspect-square', 'size-full',
    *[f'{p}grid-cols-{n}' for p in ('', 'sm:', 'md:', 'lg:', 'xl:') for n in (1, 2, 3, 4, 6, 12)],
    *[f'{p}col-span-{n}' for p in ('', 'md:', 'lg:') for n in range(1, 13)],
    *[f'{p}{d}' for p in ('', 'sm:', 'md:', 'lg:', 'xl:') for d in ('hidden', 'block', 'inline-block', 'flex')],
    *[f'{side}-{n}' for side in ('mt', 'mb', 'my', 'pt', 'pb', 'py', 'p', 'px') for n in (0, 1, 2, 4, 6, 12)],
    'mx-auto', 'text-center', 'text-left', 'text-right', 'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl',
    'text-2xl', 'font-medium', 'font-bold', 'uppercase', 'text-muted', 'text-primary', 'text-accent', 'text-danger',
    'text-success', 'text-white', 'bg-white', 'bg-gray-100', 'rounded-md', 'rounded-lg', 'border', 'w-full',
    'h-full', 'max-w-full', 'float-left', 'float-right', 'relative', 'absolute', 'overflow-hidden',
    'sw-file-pdf', 'sw-file-video', 'sw-file-web',
]


def site_class(name):
    """Classes the frontends style themselves or scripts use, not in the safelist"""
    return name.startswith(('sw-', 'ya-', 'yd-'))


def safelist_css(classes):
    """The frontends' src/backend-safelist.css for these classes"""
    names = sorted(name for name in set(classes) | set(EDITOR_VOCABULARY) if not site_class(name))
    lines = [
        '/*',
        ' * Tailwind classes used by the HTML that the backend stores, printed by django-shop\'s',
        ' * `manage.py tailwindize_html --safelist`. Tailwind only generates the classes it finds in the sources, so the',
        ' * HTML from the database can use only these. Keep this file identical in every storefront.',
        ' */',
        '',
    ]
    line = []
    for name in names:
        line.append(name)
        if len(' '.join(line)) > 100:
            lines.append(f'@source inline("{" ".join(line)}");')
            line = []
    if line:
        lines.append(f'@source inline("{" ".join(line)}");')
    return '\n'.join(lines) + '\n'


def styled_classes(soup):
    """Classes that the HTML's own <style> elements style"""
    return {name for style in soup.find_all('style') for name in re.findall(r'\.(-?[_a-zA-Z][\w-]*)', style.get_text())}


def classes_in(html):
    """Classes used in the HTML outside <svg>, except those its own <style> elements style"""
    if not html or 'class' not in html:
        return Counter()
    soup = BeautifulSoup(html, 'html.parser')
    own = styled_classes(soup)
    return Counter(name for tag in soup.find_all(True) if not in_svg(tag)
                   for name in tag.get('class') or [] if name not in own)


def read_safelist(text):
    """The classes listed in a backend-safelist.css"""
    return {name for m in re.finditer(r'@source inline\("([^"]*)"\)', text) for name in m.group(1).split()}


def group_report(reports):
    total = Report()
    for report in reports:
        total.update(report)
    by_old = defaultdict(Counter)
    for (old, new), count in total.mapped.items():
        by_old[old][new] += count
    return total, by_old
