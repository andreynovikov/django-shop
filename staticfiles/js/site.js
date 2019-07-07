/**
 * Get the value of a querystring
 * @param  {String} field The field to get the value of
 * @param  {String} url   The URL to get the value from (optional)
 * @return {String}       The field value
 */
var getQueryString = function(field, url) {
  var href = url ? url : window.location.href;
  var reg = new RegExp('[?&]' + field + '=([^&#]*)', 'i');
  var string = reg.exec(href);
  return string ? decodeURIComponent(string[1].replace(/\+/g, " ")) : null;
};

var updateQueryString = function(queryString, key, value) {
  if (typeof value === 'string')
    value = value.replace(/\s/g, "+");
  newParam = key + '=' + value;

  if (queryString) {
    var updateRegex = new RegExp('([\?&])' + key + '[^&]*');
    var removeRegex = new RegExp('([\?&])' + key + '=[^&;]+[&;]?');

    if (typeof value == 'undefined' || value == null || value == '' || value == '0') { // Remove param if value is empty
      params = queryString.replace(removeRegex, "$1");
      params = params.replace( /[&;]$/, "" );
    } else if (queryString.match(updateRegex) !== null) { // If param exists already, update it
      params = queryString.replace(updateRegex, "$1" + newParam);
    } else { // Otherwise, add it to end of query string
      params = queryString;
        if (queryString.indexOf('?') == -1)
            params += '?';
        else
            params += '&';
      params += newParam;
    }
  }

  return params;
};

function reloadNotice() {
    $("#cart_notice").load("/shop/basket/notice/", function() {
    });
}

function loadExtNotice(id) {
    $("#cart_extnotice").load("/shop/basket/extnotice/?product=" + id);
}

function reloadCompareNotice() {
    $("#compare_notice").load("/compare/notice/", function() {
    });
}

function addProduct() {
    var productIDSplitter = (this.id).split("_");
    var productID = productIDSplitter[1];
    $(this).click(function(){
        $.ajax({
            type: "GET",
            url: updateQueryString(this.href, "silent", "1"),
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

function compareProduct() {
    var link = this;
    var id = $(link).data("id");
    var comparisonLink = $(link).data("comparison-link");
    if (comparisonLink) {
        $.ajax({
            type: "GET",
            url: link.href,
            success: function(theResponse) {
                link.href = comparisonLink;
                link.innerHTML = "Сравнить";
                $(link).removeData("comparison-link");
                $(link).removeAttr("data-comparison-link");
                reloadCompareNotice();
            },
            error: function(theResponse) {
            }
        });
        return false;
    }
    return true;
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
    $('.compareProduct').click(compareProduct);
});

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
