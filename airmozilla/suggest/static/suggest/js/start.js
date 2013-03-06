/*global $:true */

$(function() {
    'use strict';

    function reset_buttons() {
        $('.delete-button:hidden').show();
        $('.delete-confirm-question:visible,' +
          '.delete-confirm:visible,' +
          '.delete-cancel:visible').hide();
    }

    $('.delete-button').click(function() {
        reset_buttons();
        var parent = $(this).parents('td.delete');
        $(this).hide();
        $('.delete-confirm-question,.delete-confirm,.delete-cancel', parent).show();
        return false;
    });

    $('.delete-confirm').click(function() {
        var parent = $(this).parents('td.delete');
        var id = parent.data('id');
        $.post('/suggest/' + id + '/delete/', function() {
            parent.parents('tr').remove();
        });
        return false;
    });

    $('.delete-cancel').click(function() {
        reset_buttons();
        return false;
    });
});
