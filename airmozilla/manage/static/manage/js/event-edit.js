/*global $:true process_vidly_status_response:true */


$(function() {
    'use strict';
    // Previously checked approval groups can not be unchecked
    $('input[name="approvals"]:checked').each(function() {
        $(this)
          .attr('disabled', 'disabled')
          .attr('title', "You can't uncheck previously requested approvals")
          .parents('label')
            .addClass('un-uncheckable')
            .append($('<small>').text("(Once checked, you can't uncheck it)"));
    });

    if ($('#vidly-submission').length) {
        var $element = $('#vidly-submission');
        $.ajax({
          url: '/manage/vidly/status/',
          data: {id: $element.data('id')},
          success: function(response) {
              process_vidly_status_response(response, $element);
          }
        });
    }


    // Autocomplete curated groups
    function process_curated_groups(element) {
        return data;
    }
    $('#id_curated_groups').select2({
        placeholder: "Search for a Mozillians group",
        minimumInputLength: 2,
        ajax: {
            url: '/manage/curated-groups-autocomplete/',
            dataType: 'json',
            data: function (term, page) {
                return {q: term};
            },
            results: function (data, page) {
                return {results: data.groups};
            }
        },
        initSelection: process_curated_groups
    });

});
