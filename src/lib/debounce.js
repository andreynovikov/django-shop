// TODO: refactor

const debounce = (func) => {
  let timer
  return function (...args) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const context = this
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      timer = null
      func.apply(context, args)
    }, 300)
  }
}

export default debounce
