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
            // then the <starred-event> tag would have the list of ids
            var serverStars = [];
            var ids = $('starred-event').data('ids');
            if (ids.length) {
                ids.split(',').forEach(function(id) {
                    serverStars.push(parseInt(id, 10));
                });
            }
            console.log('serverStats', serverStars);
            csrfToken = $('starred-event input[name="csrfmiddlewaretoken"]').val();
            // jquery array comparison http://stackoverflow.com/a/7726509/205832
            if ($(stars).not(serverStars).length === 0 &&
                $(serverStars).not(stars).length === 0) {
                Stars.sync();
            }
        }
   }

    return {

        getStars: function () {
            return stars;
        },

        sync: function () {
            if (!csrfToken) {
                return initialSync();
            } else if (signedIn) {
                $.post($('starred-event').data('post'), $.param( {
                    'ids': stars,
                    'csrfmiddlewaretoken': csrfToken
                }, true))
                .then( function(response) {
                    if (response) {
                        csrfToken = response.csrf_token;
                        stars = response.ids;
                        stars = stars.slice(0, 500);
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
                stars.unshift(id);
            }
            stars = stars.slice(0, 500);
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
        var id = $(this).data('id');
        Stars.toggleArrayPresence(id);
        $('a.star[data-id=' + id + ']').toggleClass('star-on');
    });

    Stars.sync();
});
