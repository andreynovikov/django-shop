"""
Accounts whose phone is not +7 and ten digits can't log in on the storefronts any more, see PhoneValidator.
This repairs phones typed with an extra 7 or 8 after +7, and removes accounts that hold nothing, or whose phone
is unreal and whose orders were all canceled. It only reports unless --apply is given.
"""
import re

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.db.models import F, ProtectedError

from shop.models import Order, ShopUser

VALID = re.compile(r'^\+7\d{10}$')
MISTYPED = re.compile(r'^\+7[78](\d{10})$')  # +7 8 916..., +7 7 916...
# 000, 0001, 00002 and the like: the system user, marketplaces and API users, which code looks up by phone
TECHNICAL = re.compile(r'^\d{1,9}$')

# Codes in flight, nothing of the user's
TRANSIENT = {'shop.LoginCode', 'shop.PhoneCode'}
# What an account with an unreal phone may lose. Reviews and comments stay without the user, the rest goes with it.
# Any other relation, such as one added later, keeps the account.
DISPOSABLE = {'canceled orders', 'shop.Favorites', 'reviews.Review', 'shop.ProductReview',
              'django_comments.Comment', 'django_comments.CommentFlag'}


def repaired(phone):
    """ The +7 number that a mistyped or unformatted phone stands for, if it looks like one """
    mistyped = MISTYPED.match(phone)
    if mistyped:
        return '+7' + mistyped.group(1)
    digits = re.sub(r'\D', '', phone)
    if not phone.startswith('+') and len(digits) == 11 and digits[0] in '78':  # 8 916 ..., 7-916-...
        return '+7' + digits[1:]
    return None


def is_unreal(phone):
    """ Too short or too long for a phone, or a made-up one such as +7 000 000-00-00 or +7 123 456-78-90 """
    digits = re.sub(r'\D', '', phone)
    if not 11 <= len(digits) <= 12:
        return True
    tail = digits[-10:]
    return len(set(tail)) == 1 or tail in '01234567890' or tail in '09876543210'


def holdings(user):
    """ How many rows refer to the user, by model label; orders are split into canceled ones and the rest """
    found = {}
    for relation in ShopUser._meta.related_objects:
        label = relation.related_model._meta.label
        if label in TRANSIENT:
            continue
        rows = relation.related_model._base_manager.filter(**{relation.field.name: user})
        if label == 'shop.Order' and relation.field.name == 'user':
            canceled = rows.filter(status=Order.STATUS_CANCELED).count()
            others = rows.count() - canceled
            if canceled:
                found['canceled orders'] = canceled
            if others:
                found['orders'] = others
            continue
        count = rows.count()
        if count:
            found[label if relation.field.name in ('user', 'author') else '%s.%s' % (label, relation.field.name)] = count
    return found


def describe(found):
    return ', '.join('%s %d' % item for item in found.items()) or 'nothing'


class Command(BaseCommand):
    help = 'Repairs or removes accounts whose phone is not +7 and ten digits. Reports only, unless --apply.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='make the changes, not just report them')

    def handle(self, *args, apply=False, **options):
        self.apply = apply
        self.counts = {}
        taken = set()  # numbers given by repairs earlier in this run

        legacy = ShopUser.objects.exclude(phone__regex=VALID.pattern)
        # Most recent first: when two accounts repair to one number, the one in use gets it
        for user in legacy.order_by(F('last_login').desc(nulls_last=True), '-id'):
            label = '%s (id %d)' % (user.phone, user.id)
            if TECHNICAL.match(user.phone):
                self.report('skip', label, 'technical account')
                continue
            if user.is_staff or user.is_superuser:
                self.report('skip', label, 'staff')
                continue

            note = ''
            phone = repaired(user.phone)
            if phone is not None:
                if phone not in taken and not ShopUser.objects.filter(phone=phone).exists():
                    taken.add(phone)
                    self.repair(user, phone, label)
                    continue
                note = '; %s is taken' % phone

            found = holdings(user)
            if not found:
                self.remove(user, label, 'holds nothing' + note)
            elif is_unreal(user.phone) and set(found) <= DISPOSABLE:
                self.remove(user, label, 'unreal phone, %s%s' % (describe(found), note))
            else:
                self.report('keep', label, describe(found) + note)

        summary = ', '.join('%s %d' % item for item in sorted(self.counts.items()))
        self.stdout.write('%s: %s' % ('Done' if apply else 'Dry run, nothing changed', summary or 'no legacy phones'))

    def report(self, action, label, reason):
        self.counts[action] = self.counts.get(action, 0) + 1
        self.stdout.write('%-7s %s: %s' % (action, label, reason))

    def repair(self, user, phone, label):
        if self.apply:
            try:
                with transaction.atomic():
                    # The new number is a guess until a code sent to it comes back, so the first SMS login proves it
                    ShopUser.objects.filter(pk=user.pk).update(phone=phone, phone_verified=False)
            except IntegrityError as e:  # registered meanwhile
                self.report('failed', label, '→ %s; %s' % (phone, str(e).splitlines()[0]))
                return
        self.report('repair', label, '→ %s' % phone)

    def remove(self, user, label, reason):
        if self.apply:
            try:
                with transaction.atomic():  # foreign keys are checked when it commits, tables of removed apps too
                    Order.objects.filter(user=user, status=Order.STATUS_CANCELED).delete()
                    user.delete()
            except (ProtectedError, IntegrityError) as e:
                self.report('failed', label, '%s; %s' % (reason, str(e).splitlines()[0]))
                return
        self.report('remove', label, reason)
