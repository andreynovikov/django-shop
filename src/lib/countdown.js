import { useEffect, useState } from 'react'

const declOfNum = (n, titles) => {
  return titles[(n % 10 === 1 && n % 100 !== 11) ? 0 : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 1 : 2]
}

const useCountdown = (delay) => {
  const now = new Date().getTime()
  const countdownDate = now + delay * 1000
  const [countdown, setCountdown] = useState(delay * 1000)

  useEffect(() => {
    let interval = null
    if (delay > 0) {
      interval = setInterval(() => {
        const diff = countdownDate - new Date().getTime()
        setCountdown(diff)
        if (diff < 0) {
          setCountdown(0)
          clearInterval(interval)
        } else {
          setCountdown(diff)
        }
      }, 1000)
    } else {
      setCountdown(delay * 1000)
    }

    return () => {
      if (interval !== null)
        clearInterval(interval)
    }
    /* eslint-disable react-hooks/exhaustive-deps */
  }, [delay])

  if (delay > 0 && countdown >= 0)
    return getReturnValues(countdown)
  else
    return getReturnValues(delay * 1000)
}

const getReturnValues = (countDown) => {
  const timeleft = Math.ceil(countDown / 1000)
  if (timeleft < 0)
    return [timeleft, ""]
  if (timeleft === 0)
    return [0, "через 0 секунд"]

  var text = "через "
  if (timeleft > 60) {
    const minutesleft = Math.floor(timeleft / 60)
    const secondsleft = timeleft - minutesleft * 60
    text += minutesleft + " " + declOfNum(minutesleft, ['минуту', 'минуты', 'минут'])
    if (secondsleft != 0) {
      text += " " + secondsleft + " " + declOfNum(secondsleft, ['секунду', 'секунды', 'секунд'])
    }
  } else {
    text += timeleft + " " + declOfNum(timeleft, ['секунду', 'секунды', 'секунд'])
  }

  return [timeleft, text]
}

export { useCountdown }
