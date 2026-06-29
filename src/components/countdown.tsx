import { useCountdown } from '@/lib/countdown'

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
    <div className="d-block">
      Запросить {permanentPassword ? "пароль" : "код"} повторно можно {countdownText}
    </div>
  ) : reset !== undefined && delay >= 0 && countdown === 0 ? (
    <div>
      <a className="link-primary" onClick={reset} style={{ cursor: 'pointer' }}>
        {permanentPassword ? (
          "Сбросить забытый пароль"
        ) : (
          "Прислать код повторно"
        )}
      </a></div>
  ) : ""
}