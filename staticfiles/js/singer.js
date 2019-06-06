var updateCartNotice = function() {
    $("#cart_notice").load("/shop/basket/notice");
};

$(document).ready(function() {

//$( "[class|=opener]" ).mouseover(function() {
//  $(this).children(":first").css("opacity","1");
//}).mouseout(function() {
//  $(this).children(":first").css("opacity","0.5");
//});

$('.opener-ajax').magnificPopup({
    type: 'ajax',
    tLoading: 'Загрузка...',
});
$('.opener-product').magnificPopup({
    type: 'ajax',
    closeOnBgClick: false,
    tLoading: 'Загрузка...',
    closeMarkup: '<div class="mfp-close gallery-popup-nav-item"></div>',
    mainClass: 'mfp-fade',
    removalDelay: 300
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

  $(document).on('click', '.gallery-popup-thumbs-item', function(e) {
    var clicked = $(this);
    var newSelection = clicked.data('image');
    var img = $('.gallery-popup-image');
    if (img.attr('src') == newSelection)
      return;
    img.hide();
    clicked.parent().find('.gallery-popup-thumbs-item').removeClass('selected');
    clicked.addClass('selected');
    img.attr('src', newSelection);
    img.on('load', function() {
      img.fadeIn('fast');
    });
  });
  $(document).on('load', '.gallery-popup-image', function(e) {
    e.stopPropagation();
    $(this).fadeIn('fast');
  });

  $(document).on('click', '.gallery-popup-action-prev', function(e) {
      e.stopPropagation();
      var item = $('.gallery-popup-thumbs-item.selected');
      var prev = item.prev();
      if (prev.length == 0)
        prev = item.siblings().last();
      prev.trigger('click');
    });

  $(document).on('click', '.gallery-popup-action-next', function(e) {
      e.stopPropagation();
      var item = $('.gallery-popup-thumbs-item.selected');
      var next = item.next();
      if (next.length == 0)
        next = item.siblings().first();
      next.trigger('click');
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

