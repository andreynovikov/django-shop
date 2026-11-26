"""
Prints the .env lines of an old sewingworld/settings/integrations.py, which held the integrations' credentials as
Python before they moved to .env. Run it once per deployment, as a user who can read the file, and append the output
to the deployment's .env, see "Environment setup" in deploy/README.md:

    sudo .venv/bin/python deploy/integrations_to_env.py sewingworld/settings/integrations.py | sudo tee -a .env >/dev/null

Settings it does not know are named on stderr, without their values, so nothing is dropped silently.
"""
import json
import runpy
import sys

# Settings with one value each
PLAIN = [
    'SMSRU_KEY', 'BONUSES_SMSRU_KEY', 'SMS_USLUGI_LOGIN', 'SMS_USLUGI_PASSWORD',
    'YM_COUNTER_ID', 'YM_API_TOKEN',
    'UNISENDER_KEY', 'UNISENDER_PRODUCT_REVIEW_LIST', 'UNISENDER_ABANDONED_BASKET_LIST',
]
# Dictionaries of credentials, one variable per key: RARUS['login'] is RARUS_LOGIN
FLAT = {
    'RARUS': ['login', 'password'],
    'SBER_MARKET': ['api', 'token', 'merchant_code', 'auth_user', 'auth_password'],
}
# Settings kept as JSON
STRUCTURED = ['YANDEX_DOSTAVKA']
# Settings the code doesn't read
UNUSED = ['TELEGRAM_CHANNEL_ID', 'TELEGRAM_BOT_TOKEN', 'YM_CLIENT_ID']


def line(name, value):
    value = str(value)
    # django-environ takes a value in single quotes as it is, unless it is in double quotes inside them
    if '\n' in value or (value.startswith('"') and value.endswith('"')):
        raise SystemExit(f'{name}: the value needs quoting by hand, add it to .env yourself')
    return f"{name}='{value}'"


def main(path):
    settings = {name: value for name, value in runpy.run_path(path).items() if name.isupper()}
    lines = []
    for name in PLAIN:
        if name in settings:
            lines.append(line(name, settings.pop(name)))
    for name, keys in FLAT.items():
        values = dict(settings.pop(name, {}))
        for key in keys:
            if key in values:
                lines.append(line(f'{name}_{key.upper()}', values.pop(key)))
        for key in values:
            print(f'{name}[{key!r}] is not converted', file=sys.stderr)
    for name in STRUCTURED:
        if name in settings:
            lines.append(line(name, json.dumps(settings.pop(name), ensure_ascii=False, separators=(',', ':'))))
    for name in UNUSED:
        if settings.pop(name, None) is not None:
            print(f'{name} is not used by the code and is left out', file=sys.stderr)
    for name in settings:
        print(f'{name} is not converted', file=sys.stderr)
    # A blank line first, in case .env doesn't end with a line break
    print()
    print('# Integrations, formerly sewingworld/settings/integrations.py')
    print('\n'.join(lines))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(f'usage: {sys.argv[0]} OLD_INTEGRATIONS_PY')
    main(sys.argv[1])
