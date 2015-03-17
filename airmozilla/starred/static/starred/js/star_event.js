var Stars = (function() {
    var stars = [],
        csrfToken, signedIn;

   function initialSync() {
        signedIn = !!$('starred-event').length;
        var fromBrowser = localStorage.getItem('stars');

        if (fromBrowser) {
            stars = JSON.parse(fromBrowser);
            Stars.triggerClickedStars();
        }

        if (signedIn) {
            $.getJSON($('starred-event').data('get')).then(function(response) {
                if (response) {
                    csrfToken = response.csrf_token;
                    stars = stars.concat(response.ids);
                    if (csrfToken) {
                        Stars.sync();
                    }
                }
            });
        }
   }

    return {

        getStars: function () {
            return stars;
        },

        sync: function () {
            if (!csrfToken) {
                return initialSync();
            }
            if (signedIn) {
                $.post($('starred-event').data('post'), $.param( {
                    'ids': stars,
                    'csrfmiddlewaretoken': csrfToken
                }, true))
                .then( function(response) {
                    if (response) {
                        csrfToken = response.csrf_token;
                        stars = response.ids;
                        localStorage.setItem('stars', JSON.stringify(stars));
                        Stars.triggerClickedStars();
                    }
                });
            }
        },

        triggerClickedStars: function () {
                $('a.star').each(function(i, element) {
                    var $element = $(element);
                    var index = stars.indexOf($(element).data('id'));
                    if (index > -1) {
                        $(element).addClass('star-on');
                    }
                });
        },

        toggleArrayPresence: function (id) {
            var index = stars.indexOf(id);
            if (index > -1) {
                stars.splice(index, 1);
            } else {
                stars.push(id);
            }
            localStorage.setItem('stars', JSON.stringify(stars));
            if (signedIn) {
                Stars.sync();
            }
        }
    };
}());

$(function() {

    // using this just to see what localStorage is storing
    var i = 0,
        oJson = {},
            sKey;
    for (; sKey = window.localStorage.key(i); i++) {
            oJson[sKey] = window.localStorage.getItem(sKey);
    }
    console.log(oJson);


   $('#content').on('click', 'a.star', function () {
      Stars.toggleArrayPresence($(this).data('id'));
      $(this).toggleClass('star-on');
   });

   Stars.sync();
});
