from urllib.parse import urlencode
from urllib.request import Request, urlopen
from collections import OrderedDict
import json


class Unisender(object):
    errorMessage = ''
    errorCode = ''

    def __init__(self, api_key='', lang='ru', secure=True, format='json', extra_params={}):
        self.api_key = api_key
        self.lang = lang
        self.secure = secure
        self.format = format

        self.default_params = {'api_key': api_key, 'format': format}
        self.default_params.update(extra_params)
        if secure:
            self.base_api_url = 'https://api.unisender.com/{0}/api/'.format(self.lang)
        else:
            self.base_api_url = 'http://api.unisender.com/{0}/api/'.format(self.lang)

    def run(self, method, data, params=OrderedDict()):
        url = '{0}{1}'.format(self.base_api_url, method)
        params.update(self.default_params)
        params.update(data)
        params = urlencode(self.http_build_query(params), doseq=True)
        request = Request(url, params.encode(), {"User-Agent": "PyUniSender 0.1.2"})
        response = urlopen(request)
        result = json.loads(response.read().decode())
        try:
            if 'error' in result:
                self.errorMessage = result['error']
                self.errorCode = result['code']
        except TypeError:
            pass # exception for non-iterable (boolean) types
        return result


    def http_build_query(self, params, key=None):
        """
        Re-implement http_build_query for systems that do not already have it
        """
        ret = OrderedDict()

        for name, val in params.items():
            name = name

            if key is not None and not isinstance(key, int):
                name = "%s[%s]" % (key, name)
            if isinstance(val, dict):
                ret.update(self.http_build_query(val, name))
            elif isinstance(val, list):
                ret.update(self.http_build_query(dict(enumerate(val)), name))
            elif val is not None:
                ret[name] = val

        return ret

    def sendEmail(self, email, sender_name, sender_email, subject, body, list_id,
                  attachments=None, lang=None, track_read=0, track_links=0, cc=None,
                  headers=None, images_as='user_default', error_checking=1, metadata=None):
        if lang is None:
            lang = self.lang
        data = {
            'email': email,
            'sender_name': sender_name,
            'sender_email': sender_email,
            'subject': subject,
            'body': body,
            'list_id': list_id,
            'lang': lang,
            'track_read': track_read,
            'track_links': track_links,
            'images_as': images_as,
            'error_checking': error_checking
        }
        if attachments is not None:
            data['attachments'] = attachments
        if cc is not None:
            data['cc'] = cc
        if headers is not None:
            data['headers'] = headers
        if metadata is not None:
            data['metadata'] = metadata
        return self.run('sendEmail', data)
