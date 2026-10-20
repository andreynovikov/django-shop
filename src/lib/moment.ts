/*
Global moment configuration. Import it for side effects at every rendering entry point
(app/layout.tsx, app/providers.tsx, pages/_app.tsx) so that `import moment from 'moment'`
uses Russian locale everywhere.
*/

import moment, { type MomentInput, type Moment } from 'moment'
import 'moment/locale/ru'

moment.locale('ru')
moment.updateLocale('ru', {
  monthsShort: {
    format: 'янв_фев_мар_апр_мая_июн_июл_авг_сен_окт_ноя_дек'.split('_'),
    standalone: 'янв_фев_март_апр_май_июнь_июль_авг_сен_окт_ноя_дек'.split('_')
  },
  calendar: {
    lastWeek: function (m?: MomentInput, now?: Moment) {
      if (now?.week() !== (this as unknown as Moment).week()) {
        switch ((this as unknown as Moment).day()) {
          case 0:
            return '[В прошлое] dddd'
          case 1:
          case 2:
          case 4:
            return '[В прошлый] dddd'
          case 3:
          case 5:
          case 6:
            return '[В прошлую] dddd'
          default:
            return '[В прошлое] dddd'
        }
      } else {
        if ((this as unknown as Moment).day() === 2) {
          return '[Во] dddd'
        } else {
          return '[В] dddd'
        }
      }
    }
  },
})

export default moment
