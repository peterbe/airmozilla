$(function() {
    var stars = [];

    function is_starred(id) {
        $(id).is('a.star.star-on');
    }
    function star(id) {
        $(id).toggleClass('star-on');
    }
    function unstar(id) {
        $(id).toggleClass('star');
    }
    function sync_stars() {
        // add to local storage
        $('a.star').each(function () {
            var e = $(this);
            var id = e.data('id');
            e.toggleClass('star-on', is_starred(id));
        });
    }

    $('.entry-summary').on('click','a.star', function () {
        var e = $(this);
        var id = e.data('id');
        console.log(e);
        console.log(id);
        stars.push(id);
        console.log(stars);

        if (is_starred(id))
            unstar(id);
        else
            star(id);

        e.toggleClass('star-on');
    });
});
