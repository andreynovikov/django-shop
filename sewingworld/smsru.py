from urllib.request import urlopen
from urllib.error import URLError
from urllib.parse import urlencode

class Client(object):
    SEND_STATUS = {
        100: "Сообщение принято к отправке",
        200: "Неправильный api_id",
        201: "Не хватает средств на лицевом счету",
        202: "Неправильно указан получатель",
        203: "Нет текста сообщения",
        204: "Имя отправителя не согласовано с администрацией",
        205: "Сообщение слишком длинное (превышает 8 СМС)",
        206: "Будет превышен или уже превышен дневной лимит на отправку сообщений",
        207: "На этот номер (или один из номеров) нельзя отправлять сообщения, либо указано более 100 номеров в списке получателей",
        208: "Параметр time указан неправильно",
        209: "Вы добавили этот номер (или один из номеров) в стоп-лист",
        210: "Используется GET, где необходимо использовать POST",
        211: "Метод не найден",
        220: "Сервис временно недоступен, попробуйте чуть позже.",
        300: "Неправильный token (возможно истек срок действия, либо ваш IP изменился)",
        301: "Неправильный пароль, либо пользователь не найден",
        302: "Пользователь авторизован, но аккаунт не подтвержден (пользователь не ввел код, присланный в регистрационной смс)",
    }

    STATUS_STATUS = {
        -1: "Message not found",
        100: "Message is in the queue",
        101: "Message is on the way to the operator",
        102: "Message is on the way to the recipient",
        103: "Message delivered",
        104: "Message failed: out of time",
        105: "Message failed: cancelled by the operator",
        106: "Message failed: phone malfunction",
        107: "Message failed, reason unknown",
        108: "Message declined",
    }

    COST_STATUS = {
        100: "Success"
    }

    config = {}

    def __init__(self, key):
      self.config['key'] = key

    def _call(self, method, args):
        """Calls a remote method."""
        if not isinstance(args, dict):
            raise ValueError("Args must be a dictionary")
        args['api_id'] = self.config['key']
        args['from'] = 'SEWINGWORLD'

        url = "http://sms.ru/%s?%s" % (method, urlencode(args))
        import sys
        print(url, file=sys.stderr)
        res = urlopen(url).read().decode('utf-8')
        print(res, file=sys.stderr)
        return res.strip().split('\n')

    def send(self, to, message, express=False, test=False):
        """Sends the message to the specified recipient. Returns a numeric
        status code, its text description and, if the message was successfully
        accepted, its reference number."""
        args = {"to": to, "text": message.encode("utf-8")}
        if "sender" in self.config:
            args["from"] = self.config["sender"]
        if express:
            args["express"] = "1"
        if test:
            args["test"] = "1"
        res = self._call("sms/send", args)
        if res[0] != "100":
            res.append(None)
        return {
            'code': int(res[0]),
            'descr': Client.SEND_STATUS.get(int(res[0]), "Unknown status"),
            'msg': res[1]
        }

    def status(self, msgid):
        """Returns message status."""
        res = self._call("sms/status", {"id": msgid})
        code = int(res[0])
        text = Client.STATUS_STATUS.get(code, "Unknown status")
        return code, text

    def cost(self, to, message):
        """Prints the cost of the message."""
        res = self._call("sms/cost", {"to": to, "text": message.encode("utf-8")})
        if res[0] != "100":
            res.extend([None, None])
        return int(res[0]), Client.COST_STATUS.get(int(res[0]), "Unknown status"), res[1], res[2]

    def balance(self):
        """Returns your current balance."""
        res = self._call("my/balance", {})
        if res[0] == "100":
            return float(res[1])
        raise Exception(res[0])

    def limit(self):
        """Returns the remaining message limit."""
        res = self._call("my/limit", {})
        if res[0] == "100":
            return int(res[1])
        raise Exception(res[0])
