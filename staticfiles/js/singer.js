$(document).ready(function() {

$( "[class|=opener]" ).mouseover(function() {
  $(this).children(":first").css("opacity","1");
}).mouseout(function() {
  $(this).children(":first").css("opacity","0.5");
});

$('.opener-ajax').magnificPopup({
        type: 'ajax'
});
$('.opener').magnificPopup({
 type: 'inline',
 fixedContentPos: false,
 fixedBgPos: true,
 overflowY: 'auto',
 closeBtnInside: true,
 preloader: false,
 midClick: true,
 removalDelay: 300
});

$('.popup-gallery').magnificPopup({
 delegate: 'a',
 type: 'image',
 tLoading: 'Çàãðóæàåòñÿ ôîòî #%curr%...',
 mainClass: 'mfp-img-mobile',
 gallery: {
  enabled: true,
  navigateByImgClick: true,
  preload: [0,1]
 },
 image: {
  tError: '<a href="%url%">Ôîòî #%curr%</a> íå çàãðóçèëîñü.',
  titleSrc: function(item) {
//   return '@@name@@';
   return '';
  }
 }
});

});

  $(document).on('click', '.selectbox', function(e) {
    e.stopPropagation();
    $('.dropdown', this).toggle();
  });

  $('html').on('click', function() {
    if ($('.dropdown').is(':visible')) {
      $('.dropdown').hide();
    }
  });
$('#navigation > div').hover(

        function(){
            if ( 768 < $(window).width() ) {
                $(this).stop().addClass('hover');
                $(this).children('.megaMenu').fadeIn('fast');
            }
        },
        function(){
            $(this).stop().removeClass('hover');
            $(this).children('.megaMenu').fadeOut('fast');

            if ($('.dropdown').is(':visible')) {
              $('.dropdown').hide();
            }
        }
    );

function delayShowPasswordReset(what) {
    timer(240000, function(timeleft) {
        if (timeleft > 60) {
            var minutesleft = Math.floor(timeleft/60);
            timeleft = timeleft - minutesleft * 60;
            var text = "Запросить " + what + " повторно можно через "
                + minutesleft + " " + declOfNum(minutesleft, ['минуту','минуты','минут']);
            if (timeleft != 0) {
                text += " " + timeleft  + " " + declOfNum(timeleft, ['секунду','секунды','секунд']);
            }
            text += ".";
            $("#reset-counter").text(text);
        } else {
            $("#reset-counter").text("Запросить " + what + " повторно можно через "
                                     + timeleft + " " + declOfNum(timeleft, ['секунду','секунды','секунд']) + ".");
        }
    }, function() {
        $("#reset-counter").text("");
        $("#password-help").addClass("hide").hide();
        $("#reset-password").removeClass("hide").show();
    });
}

function timer(time, update, complete) {
    var start = new Date().getTime();
    var interval = setInterval(function() {
        var now = time - (new Date().getTime() - start);
        if (now <= 0) {
            clearInterval(interval);
            complete();
        } else update(Math.ceil(now/1000));
    }, 100);
}

function declOfNum(n, titles) {
    return titles[(n % 10 === 1 && n % 100 !== 11) ? 0 : n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20) ? 1 : 2]
}
