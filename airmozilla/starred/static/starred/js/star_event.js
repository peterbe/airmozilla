$(function() {
    $('.entry-summary').on('click','a.star', function () {
        console.log($(this));
        $(this).toggleClass('star-off');
    });
});
