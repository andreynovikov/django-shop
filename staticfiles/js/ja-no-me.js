$(document).ready(function() {


$("#tabs").tabs({ heightStyle: "content" });

$( "[class|=opener]" ).mouseover(function() {
  $(this).children(":first").css("opacity","1");
}).mouseout(function() {
  $(this).children(":first").css("opacity","0.3");
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

$( ".accordion" ).accordion({
  active:false,
  collapsible: true,
  heightStyle: "content"
});

$('#doSearch').click(function() {
var text= $("#searchfield").val() ;
//var text=encodeURIComponent( $("#searchfield").val() );
$("#hidsearch").val(text);
});

$('#gocart').click(function() {
  location.href = '/cgi-bin/basket.cgi';
});

$('#continue').click(function() {
  $.unblockUI();
  return false;
});

$(".tobasket").click(function() {
  var productIDSplitter = (this.id).split("_");
  var productID = productIDSplitter[1];
  $.blockUI({
    message: $('img#loader'),
    fadeOut: 0,
    css: {
      left: ($(window).width() - 160) / 2 + 'px',
      top:  ($(window).height() - 24) / 2 + 'px',
      border: 'none',
      backgroundColor: 'transparent',
      width: '160px'
    }
  });
  $.ajax({
    type: "GET",
    url: "/cgi-bin/basket.cgi",
    data: { pid: productID, act_add: "1", suspend: "0"},
    success: function(theResponse) {
      $.blockUI({
        message: $('#cartinfo'),
             fadeIn: 0,
             fadeOut: 700,
             overlayCSS: { backgroundColor: '#bcd8ed' },
             css: {
                 border: '1px solid #444444',
                 width: '400px',
                 padding: '15px',
                 backgroundColor: '#bcd8ed',
                 '-webkit-border-radius': '10px',
                 '-moz-border-radius': '10px',
                 opacity: .9,
                 color: '#fff'
             }
      });
      $("#cartcell").load("/cgi-bin/bticker.cgi");
    },
    error: function(theResponse) {
      $.unblockUI();
    }
  });
  return false;
});

});
