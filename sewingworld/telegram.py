"""
Posts to the staff channel through the Telegram Bot API: TELEGRAM_BOT_TOKEN and TELEGRAM_STAFF_CHAT in .env.
"""
import logging

from django.conf import settings
from django.views.decorators.debug import sensitive_variables

import requests

log = logging.getLogger('shop')

API_URL = 'https://api.telegram.org/bot{token}/{method}'
MAX_LENGTH = 4096  # characters of a message's text


class TelegramError(Exception):
    """ A post that failed. retry_after is the seconds Telegram asks to wait when it limits the rate """

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


@sensitive_variables()  # the token, in the URL and in requests' exceptions too
def send_message(text, chat=None):
    """
    Posts the text, cut to Telegram's length, to the chat (the staff channel by default). Without a token or chat it
    logs the text and posts nothing. Raises TelegramError without the URL, which holds the token, in its message.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    chat = chat or settings.TELEGRAM_STAFF_CHAT
    if not token or not chat:
        log.info('Telegram is not configured, not posted: %s', text)
        return None
    if len(text) > MAX_LENGTH:
        text = text[:MAX_LENGTH - 1] + '…'
    url = API_URL.format(token=token, method='sendMessage')
    payload = {'chat_id': chat, 'text': text, 'link_preview_options': {'is_disabled': True}}
    try:
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
    except (requests.RequestException, ValueError) as e:
        # requests' messages name the URL, so only the kind of failure is kept
        raise TelegramError(f'Telegram: {type(e).__name__}') from None
    if not result.get('ok'):
        retry_after = (result.get('parameters') or {}).get('retry_after')
        raise TelegramError(f"Telegram: {response.status_code} {result.get('description', '')}", retry_after)
    return result.get('result')
