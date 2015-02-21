$(document).ready(function(){
    $(".entry-summary").on("click", function () {
        $(this).children().toggleClass("star-off");
    });
});
