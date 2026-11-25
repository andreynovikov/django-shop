#!/usr/bin/env python3
"""Count the hits of the legacy rewrites in a site's nginx config, to tell which of them can go.

The server block marks the rewrites to watch with two `set` directives. Each rule between them ends processing
(`last`, `break`, `redirect` or `permanent`), so the second `set` runs only when no rule matched, and otherwise the
variable keeps the URI that the rule matched:

    set $legacy_uri $uri;
    rewrite ^/shops.html$ /stores/ permanent;
    ...
    set $legacy_uri "";

A log of their own keeps those requests. The log_format goes at the top of the site's config, which is the http
level. The access_log goes into the server block, and into every location there that has an access_log of its own
(`access_log off` included), because such a location doesn't inherit the server's logs:

    log_format legacy_redirects escape=json '{"time":"$time_iso8601","uri":"$legacy_uri","status":$status,'
        '"location":"$sent_http_location","rewritten":"$uri","referer":"$http_referer",'
        '"ua":"$http_user_agent","ip":"$remote_addr"}';
    access_log /var/log/nginx/www.sewing-world.ru_legacy.jsonl legacy_redirects if=$legacy_uri;

The name doesn't end in .log, so Debian's logrotate for nginx, which keeps 14 days, leaves the file alone. The
playbook's nginx-legacy.logrotate rotates it monthly instead and keeps a year of it.

This script reads the rules from the config, replays each logged URI through them as nginx does, and reports for
each rule its hits, the clients and the pages that link to it. Run it on the server, with read access to the logs
(the group adm):

    python3 legacy_redirects.py /etc/nginx/sites-available/www.sewing-world.ru.conf \\
        /var/log/nginx/www.sewing-world.ru_legacy.jsonl*
"""
import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import unquote, urlsplit

MARKER = '$legacy_uri'
FLAGS = ('last', 'break', 'redirect', 'permanent')
REDIRECTS = ('redirect', 'permanent')

# What nginx reads from a config: blanks, a comment, a quoted string, the end of a directive or a brace, a bare word
TOKEN = re.compile(r'''(\s+)|(#[^\n]*)|"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)'|([;{}])|((?:[^\s;{}"'\\]|\\.)+)''', re.S)
PUNCTUATION, WORDS = 5, (3, 4, 6)
# nginx turns these escapes into characters and keeps the backslash of any other, such as \d or \.
ESCAPE = re.compile(r'''\\(["'\\tnr])''')
ESCAPED = {'t': '\t', 'n': '\n', 'r': '\r'}
# $1, $name and ${name} in a replacement. nginx takes a single digit after $.
VARIABLE = re.compile(r'\$(?:\{(\w+)\}|([0-9])|([A-Za-z_]\w*))')
# A rough split of clients: crawlers, link checkers and scripts, against browsers
BOT = re.compile(r'bot|crawl|spider|slurp|yandex|google|bing|baidu|semrush|ahrefs|mj12|petal|bytespider|'
                 r'facebookexternalhit|python|curl|wget|http-?client|okhttp|go-http|java/|libwww|headless|scan', re.I)


@dataclass
class Rule:
    number: int
    line: int
    pattern: str
    replacement: str
    flag: str
    regex: re.Pattern


@dataclass
class Hits:
    count: int = 0
    bots: int = 0
    first: str = ''
    last: str = ''
    addresses: set = field(default_factory=set)
    browser_addresses: set = field(default_factory=set)
    statuses: Counter = field(default_factory=Counter)
    uris: Counter = field(default_factory=Counter)
    # 'none', 'ours' or 'other', for all hits and for those from browsers
    referer_kinds: Counter = field(default_factory=Counter)
    browser_referer_kinds: Counter = field(default_factory=Counter)
    # The referers of the kinds 'ours' and 'other'
    referers: defaultdict = field(default_factory=lambda: defaultdict(Counter))
    # Hits that nginx sent elsewhere than the replay did, so the replay doesn't read some rule as nginx does
    mismatches: Counter = field(default_factory=Counter)

    def add(self, entry, own_hosts):
        self.count += 1
        time, ip, ua = entry.get('time', ''), entry.get('ip', ''), entry.get('ua', '')
        self.first = min(self.first or time, time)
        self.last = max(self.last, time)
        self.addresses.add(ip)
        referer = entry.get('referer', '')
        kind = referer_kind(referer, own_hosts)
        self.referer_kinds[kind] += 1
        if kind != 'none':
            self.referers[kind][referer] += 1
        if not ua or BOT.search(ua):
            self.bots += 1
        else:
            self.browser_addresses.add(ip)
            self.browser_referer_kinds[kind] += 1
        self.statuses[entry.get('status')] += 1
        self.uris[entry['uri']] += 1


def directives(text, path):
    """Yield (line, words, end) for each directive as nginx reads it, where end is ';', '{' or '}'."""
    words, start, line, pos = [], 0, 1, 0
    for m in TOKEN.finditer(text):
        if m.start() != pos:
            break
        pos = m.end()
        if m.lastindex == PUNCTUATION:
            yield start or line, words, m[PUNCTUATION]
            words, start = [], 0
        elif m.lastindex in WORDS:
            words.append(ESCAPE.sub(lambda e: ESCAPED.get(e[1], e[1]), m[m.lastindex]))
            start = start or line
        line += m[0].count('\n')
    if pos != len(text):
        raise SystemExit(f'{path}:{line}: cannot read the config here')


def read_rules(path):
    """The rewrites between `set $legacy_uri $uri;` and `set $legacy_uri "";`, in their order."""
    with open(path, encoding='utf-8') as f:
        text = f.read()
    rules, inside = [], False
    for line, words, end in directives(text, path):
        if words == ['set', MARKER, '$uri'] and end == ';':
            inside = True
        elif words == ['set', MARKER, ''] and end == ';' and inside:
            return rules
        elif inside:
            rules.append(read_rule(path, line, words, end, len(rules) + 1))
    raise SystemExit(f'{path}: found no rewrites between set {MARKER} $uri; and set {MARKER} "";')


def read_rule(path, line, words, end, number):
    if end != ';' or words[:1] != ['rewrite'] or len(words) not in (3, 4):
        raise SystemExit(f'{path}:{line}: only rewrite directives can stand between the two set {MARKER}')
    pattern, replacement, flag = words[1], words[2], ''.join(words[3:])
    if not flag and replacement.startswith(('http://', 'https://', '$scheme')):
        flag = 'redirect'  # nginx redirects at once
    if flag not in FLAGS:
        raise SystemExit(f'{path}:{line}: the rule needs one of the flags {", ".join(FLAGS)}. Without it nginx goes on '
                         f'to the next directives, and the request isn\'t tagged.')
    try:
        # Python spells a named group (?P<name>...)
        regex = re.compile(re.sub(r'\(\?<(?![=!])', '(?P<', pattern))
    except re.error as e:
        raise SystemExit(f'{path}:{line}: Python cannot read the regular expression: {e}')
    return Rule(number, line, pattern, replacement, flag, regex)


def replay(uri, rules):
    """The rule that nginx applies to the URI and where it sends the request, or (None, None)."""
    for rule in rules:
        m = rule.regex.search(uri)
        if m:
            return rule, expand(rule.replacement, m)
    return None, None


def expand(replacement, match):
    """The replacement with the match's captures put in. Other variables stay as they are."""
    def value(v):
        name = v[1] or v[2] or v[3]
        if name.isdigit():
            return (match[int(name)] or '') if int(name) <= match.re.groups else ''
        groups = match.groupdict()
        return (groups[name] or '') if name in groups else v[0]
    return VARIABLE.sub(value, replacement)


def path_of(url):
    """The decoded path of a URL, without the host that nginx adds to a redirect and the arguments it carries over."""
    return unquote(urlsplit(url).path)


def referer_kind(referer, own_hosts):
    if not referer or referer == '-':
        return 'none'
    host = (urlsplit(referer).hostname or '').lower()
    return 'ours' if any(host == h or host.endswith('.' + h) for h in own_hosts) else 'other'


def read_logs(paths, rules, own_hosts):
    """Hits of each rule, keyed by its number, hits that no rule matches and the number of unreadable lines."""
    hits = {rule.number: Hits() for rule in rules}
    unmatched, unreadable = Hits(), 0
    for path in paths:
        opener = gzip.open if path.endswith('.gz') else open
        with opener(path, 'rt', encoding='utf-8', errors='replace') as f:
            for text in f:
                try:
                    entry = json.loads(text)
                    uri = entry['uri']
                except (ValueError, KeyError, TypeError):
                    unreadable += 1
                    continue
                rule, target = replay(uri, rules)
                if rule is None:
                    unmatched.add(entry, own_hosts)
                    continue
                hits[rule.number].add(entry, own_hosts)
                sent = entry.get('location' if rule.flag in REDIRECTS else 'rewritten') or ''
                if path_of(sent) != path_of(target):
                    hits[rule.number].mismatches[f'{uri} → {sent}, replay {target}'] += 1
    return hits, unmatched, unreadable


def show(title, counter, top):
    if counter:
        print(f'    {title}:')
        for value, n in counter.most_common(top):
            print(f'      {n:7}  {value}')


def describe(hits, top):
    print(f'    {hits.count} hits from {len(hits.addresses)} addresses, {hits.first[:10]} to {hits.last[:10]}')
    print(f'    browsers {hits.count - hits.bots} from {len(hits.browser_addresses)} addresses, bots {hits.bots}')
    print('    status ' + ', '.join(f'{status} ×{n}' for status, n in hits.statuses.most_common()))
    kinds = hits.referer_kinds
    print(f'    referer: none {kinds["none"]}, our pages {kinds["ours"]}, other sites {kinds["other"]}')
    show('URIs', hits.uris, top)
    show('our pages', hits.referers['ours'], top)
    show('other sites', hits.referers['other'], top)
    show(f'{hits.mismatches.total()} hits that nginx sent elsewhere than the replay', hits.mismatches, top)


def summary(rules, hits):
    def numbers(test):
        return ' '.join(f'#{rule.number}' for rule in rules if test(hits[rule.number])) or '-'

    print('\nSummary')
    print(f'  No hits: {numbers(lambda h: not h.count)}')
    print(f'  Only bots: {numbers(lambda h: h.count and h.bots == h.count)}')
    print(f'  Browsers through links on other sites: {numbers(lambda h: h.browser_referer_kinds["other"])}')
    print(f'  Browsers without a referer (bookmarks, typed URLs, apps): '
          f'{numbers(lambda h: h.browser_referer_kinds["none"])}')
    print(f'  Our own pages link to them: {numbers(lambda h: h.referer_kinds["ours"])}')
    print(f'  The replay differs from nginx: {numbers(lambda h: h.mismatches)}')


def report(rules, hits, unmatched, unreadable, top):
    found = [h for h in [*hits.values(), unmatched] if h.count]
    if found:
        first, last = min(h.first for h in found), max(h.last for h in found)
        try:
            days = f', {(datetime.fromisoformat(last) - datetime.fromisoformat(first)).days} days'
        except ValueError:
            days = ''
        print(f'Hits from {first} to {last}{days}')
    else:
        print('The logs have no hits')
    if unreadable:
        print(f'{unreadable} lines of the logs are not entries of the legacy_redirects format')
    for rule in rules:
        print(f'\n#{rule.number}  line {rule.line}  {rule.pattern} → {rule.replacement} ({rule.flag})')
        if hits[rule.number].count:
            describe(hits[rule.number], top)
        else:
            print('    no hits')
    if unmatched.count:
        print(f'\n{unmatched.count} hits match no rule in the config, so their rules have changed or gone since')
        describe(unmatched, top)
    summary(rules, hits)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('config', help="the site's nginx config")
    parser.add_argument('logs', nargs='+', help='the logs in the legacy_redirects format, .gz ones too')
    parser.add_argument('--own-host', action='append',
                        help='a host whose pages, and its subdomains\', are ours (default: sewing-world.ru)')
    parser.add_argument('--top', type=int, default=5, help='how many URIs and referers to show for a rule')
    args = parser.parse_args()
    rules = read_rules(args.config)
    hits, unmatched, unreadable = read_logs(args.logs, rules, args.own_host or ['sewing-world.ru'])
    report(rules, hits, unmatched, unreadable, args.top)


if __name__ == '__main__':
    main()
