import { useCountdown } from '@/lib/countdown'

// delay is the backend's retry_after: seconds until another code can be sent (4 minutes after one was, see
// OneTimeCode in django-shop), 0 when one can be sent at once, -1 while one is being requested. For the first minute
// it says that the code was sent, then counts down, then offers reset: another code, or with a permanent password a
// code that replaces the forgotten password.
export default function Countdown({
  delay,
  permanentPassword = false,
  reset,
}: {
  delay: number
  permanentPassword: boolean
  reset?: () => void
}) {
  const [countdown, countdownText] = useCountdown(delay)

  return countdown > 180 ? (
    <span className="text-warning">
      Код выслан на указанный телефон по смс
    </span>
  ) : countdown > 0 ? (
    <div className="block">
      Запросить {permanentPassword ? "пароль" : "код"} повторно можно {countdownText}
    </div>
  ) : reset !== undefined && delay >= 0 && countdown === 0 ? (
    <div>
      <a className="text-primary hover:text-link-hover" onClick={reset}>
        {permanentPassword ? (
          "Сбросить забытый пароль"
        ) : (
          "Прислать код повторно"
        )}
      </a></div>
  ) : ""
}