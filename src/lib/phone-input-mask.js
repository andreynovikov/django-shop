import Inputmask from 'inputmask'

const phoneInputMask = Inputmask({
  mask: ["(999) 999-99-99", "* (999) 999-99-99"],
  definitions: {
    "*": { validator: "[78]" }
  },
  onBeforePaste: function (pastedValue) {
    return pastedValue.replace(/(\+7|\-\s)/, "")
  },
  onBeforeMask: function (value) {
    return value.replace(/(\+7|\-\s)/, "")
  },
  oncomplete: function () {
    var value = this.inputmask.unmaskedvalue()
    if (value.length > 10) {
      value = value.substr(1)
      this.inputmask.setValue(value)
    }
  },
  keepStatic: true,
})

export default phoneInputMask