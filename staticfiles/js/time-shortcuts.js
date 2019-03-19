(function ($) {
    $(document).ready(function () {

        DateTimeShortcuts.clockHours.default_ = [];

        for (let hour = 0; hour <= 23; hour++) {
            for (let minute = 0; minute <= 45; minute+=15) {
                let verbose_name = new Date(1970, 1, 1, hour, minute, 0).strftime('%H:%M');
                DateTimeShortcuts.clockHours.default_.push([verbose_name, hour + minute / 100])
            }
        }

        DateTimeShortcuts.handleClockQuicklink = function(num, val) {
            var d;
            if (val === -1) {
                d = DateTimeShortcuts.now();
            }
            else {
                var hour = Math.floor(val);
                var minute = Math.round(val * 100) - hour * 100;
                d = new Date(1970, 1, 1, hour, minute, 0, 0);
            }
            DateTimeShortcuts.clockInputs[num].value = d.strftime(get_format('TIME_INPUT_FORMATS')[0]);
            DateTimeShortcuts.clockInputs[num].focus();
            DateTimeShortcuts.dismissClock(num);
        }

    });
})(django.jQuery);
