from http.client import HTTPSConnection
from urllib.error import URLError
from urllib.parse import urlencode

import json

class Client(object):
    config = {}

    def __init__(self, login, password):
      self.config['login'] = login
      self.config['password'] = password

    def _call(self, args):
        """Calls a remote method."""
        if not isinstance(args, dict):
            raise ValueError("Args must be a dictionary")
        args['login'] = self.config['login']
        args['password'] = self.config['password']

        host = "lcab.sms-uslugi.ru"
        url = "/lcabApi/sendSms.php"
        values = urlencode(args)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
            }
        conn = HTTPSConnection(host)
        conn.request('POST', url, values, headers)
        response = conn.getresponse()
        data = response.read()
        return json.loads(data.decode('utf-8'))

    def send(self, to, message, express=False, check=False):
        """Sends the message to the specified recipient. Returns a numeric
        status code, its text description and, if the message was successfully
        accepted, its reference number."""
        args = {"to": to, "txt": message.encode("utf-8")}
        if check:
            args["check"] = "1"
        result = self._call(args)
        return result
