function revert (tag) {
    console.log('reverting', tag);
    console.log($('#revisions').data('revert'));
    $.post($('#revisions').data('revert'), {
        tag: tag,
        event_id: $('#revisions').data('event'),
        csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
    })
    .done(function (data) {
        console.log('Done!', data);
    })
    .fail(function (data) {
        // error
    });
}
