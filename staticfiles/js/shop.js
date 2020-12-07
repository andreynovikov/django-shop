var shop = (function () {
    'use strict';

    var reloadCartNotice = function() {
        $('#cart-holder').load('/shop/basket/notice/', function(){});
    }

    var reloadCompareNotice = function() {
        $("#compare-notice").load("/compare/notice/", function() {});
    }

    var reloadFavoritesNotice = function() {
        $("#favorites-notice").load("/shop/favorites/notice/", function() {});
    }

    return {
        reloadCartNotice: reloadCartNotice,
        reloadCompareNotice: reloadCompareNotice,
        reloadFavoritesNotice: reloadFavoritesNotice
    }
})();

(function () {
    'use strict';

    function addToCart() {
        var $link = $(this);
        var $spinner = $link.find('> .spinner-border');
        var $icon = $link.find('> .czi-cart');
        $spinner.removeClass('d-none');
        $icon.addClass('d-none');
        var id = $link.data('id');
        var url = sworld.updateQueryString(this.href, 'silent', '1');
        var $qf = $link.siblings('.quantity-input');
        if ($qf[0] && $qf[0].value > 1)
            url = sworld.updateQueryString(url, 'quantity', $qf[0].value);
        $.ajax({
            type: 'GET',
            url: url,
            success: function(theResponse) {
                shop.reloadCartNotice();
                $spinner.addClass('d-none');
                $icon.removeClass('d-none');
                $('#cart-toast').toast('show');
            },
            error: function(theResponse) {
                console.log(theResponse);
            }
        });
        return false;
    }

    function removeFromCart() {
        var link = this;
        $.ajax({
            type: 'GET',
            url: sworld.updateQueryString(this.href, 'silent', '1'),
            success: function(theResponse) {
                shop.reloadCartNotice();
            },
            error: function(theResponse) {
                console.log(theResponse);
            }
        });
        return false;
    }

    function compareProduct() {
        var $link = $(this);
        var id = $link.data("id");
        var comparisonLink = $link.data("comparison-link");
        if (!comparisonLink)
            return true;
        $.ajax({
            type: "GET",
            url: this.href,
            success: function(theResponse) {
                $link.prop("href", comparisonLink);
                $link.children("span").text("Сравнение");
                $link.removeClass("btn-secondary");
                $link.addClass("btn-accent");
                $link.removeData("comparison-link");
                $link.removeAttr("data-comparison-link");
                shop.reloadCompareNotice();
            },
            error: function(theResponse) {
                console.log(theResponse);
            }
        });
        return false;
    }

    function quickViewProduct() {
        var $link = $(this);
        var title = $link.data('title');
        var href = $link.data('href');
        $.get(this.href, function(data) {
            var $quickView = $('#quick-view');
            $quickView.find('.modal-header .product-title span').text(title);
            $quickView.find('.modal-header .product-title a').attr('href', href);
            $quickView.find('.modal-body').html(data);

            var $productCard = $link.closest('.product-card').parent();
            var $prev = $productCard.prev();
            var $next = $productCard.next();

            var $prevQuickViewLink = $('#prev-quick-view-link');
            if ($prev.length) {
                $prevQuickViewLink.off('click');
                $prevQuickViewLink.on('click', function() {
                    $prev.find('a.product-quick-view').trigger('click');
                    return false;
                });
                $prevQuickViewLink.removeClass('d-none');
            } else {
                $prevQuickViewLink.addClass('d-none');
            }

            var $nextQuickViewLink = $('#next-quick-view-link');
            if ($next.length) {
                $nextQuickViewLink.off('click');
                $nextQuickViewLink.on('click', function() {
                    $next.find('a.product-quick-view').trigger('click');
                    return false;
                });
                $nextQuickViewLink.removeClass('d-none');
            } else {
                $nextQuickViewLink.addClass('d-none');
            }

            $quickView.modal('show');
        });
        return false;
    }

    function favoritizeProduct() {
        var $this = $(this);
        var isButton = $(this).is("button");
        var id = $this.data("id");
        var favoritesLink = $this.data("favorites-link");
        if (!favoritesLink)
            return true;
        console.log(this.href);
        console.log($this.attr("href"));
        $.ajax({
            type: "GET",
            url: $this.attr("href"),
            success: function(theResponse) {
                $this.attr("href", favoritesLink);
                $this.removeData("favorites-link");
                $this.removeAttr("data-favorites-link");
                if (isButton) {
                    $this.children("span").attr("data-original-title", "В избранном");
                    $this.addClass("bg-accent");
                    $this.addClass("text-light");
                } else {
                    $this.children("span").text("В избранном");
                    $this.removeClass("btn-secondary");
                    $this.addClass("btn-accent");
                }
                shop.reloadFavoritesNotice();
            },
            error: function(theResponse) {
                console.log(theResponse);
            }
        });
        return false;
    }

    $(document).on('click', '.add-to-cart', addToCart);
    $(document).on('click', '.remove-from-cart', removeFromCart);
    $(document).on('click', '.compare-product', compareProduct);
    $(document).on('click', '.product-quick-view', quickViewProduct);
    $(document).on('click', '.favoritize-product', favoritizeProduct);
}());
