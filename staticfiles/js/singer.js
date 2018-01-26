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
 tLoading: 'Загружается фото #%curr%...',
 mainClass: 'mfp-img-mobile',
 gallery: {
  enabled: true,
  navigateByImgClick: true,
  preload: [0,1]
 },
 image: {
  tError: '<a href="%url%">Фото #%curr%</a> не загрузилось.',
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

