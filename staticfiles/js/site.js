function setProductOpener(selector) {
    $(selector).find('.opener-product').magnificPopup({
        type: 'ajax',
        closeOnBgClick: false,
        tLoading: 'Загрузка...',
        closeMarkup: '<div class="mfp-close gallery-popup-nav-item"></div>',
        mainClass: 'mfp-fade',
        removalDelay: 300
    });
}

$(document).ready(function() {

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

});
