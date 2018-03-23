function reloadNotice() {
    $("#cart_notice").load("/shop/basket/notice/", function() {
       //$("#cart_notice a").each(function(index) {
        //    var href = $(this).attr("href")
        //    $(this).attr('href', "https://order.sewing-world.ru" + href);
        //});
    });
}

function loadExtNotice(id) {
    $("#cart_extnotice").load("/shop/basket/extnotice/?product=" + id);
}

function addProduct() {
    var productIDSplitter = (this.id).split("_");
    var productID = productIDSplitter[1];
    $(this).click(function(){
        $.ajax({
            type: "GET",
            //url: "https://order.sewing-world.ru/shop/basket/add/" + productID + "/?silent=1",
            url: "/shop/basket/add/" + productID + "/?silent=1",
            success: function(theResponse) {
                reloadNotice();
                loadExtNotice(productID);
                $.magnificPopup.open({
                    items: {
                        src: '#sw-cartinfo',
                        type: 'inline'
                    }
                });
            },
            error: function(theResponse) {
                $.magnificPopup.close();
            }
        });
        return false;
    });
}

$(document).ready(function() {
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
        tLoading: 'гЮЦПСФЮЕРЯЪ ТНРН #%curr%...',
        mainClass: 'mfp-img-mobile',
        gallery: {
            enabled: true,
            navigateByImgClick: true,
            preload: [0,1]
        },
        image: {
            tError: '<a href="%url%">тНРН #%curr%</a> МЕ ГЮЦПСГХКНЯЭ.',
            titleSrc: function(item) {
                //   return '@@name@@';
                return '';
            }
        }
    });

    $('#gocart').click(function() {
        location.href = '/shop/basket/';
    });

    $('#continue').click(function() {
        $.magnificPopup.close();
        return false;
    });

    $('.addProduct').each(addProduct);
});
