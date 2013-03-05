$(function() {
    $('p.help-block').each(function() {
        $(this).hide();
        var $controls = $(this).parents('.control-group');
        console.log($controls);
       $('textarea,input', $controls)
        //$controls
          .attr('title', $(this).text())
          .addClass('tooltip');
    });
    $('.tooltip').tooltipster({
       position: 'top'
    });
});
