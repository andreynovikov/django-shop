from shop.tasks import send_message


class Gateway:
    @staticmethod
    def make_call(device, token):
        raise NotImplementedError

    @staticmethod
    def send_sms(device, token):
        send_message.delay(device.number.as_e164, 'Токен доступа: {}'.format(token))
