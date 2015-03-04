
$(function() {
    var stars = [],
    csrfToken,
    signedIn = !!$('starred-event').length,
    from_browser = localStorage.getItem('stars');

   function triggerClickedStars() {
        $('a.star').each(function(i, element) {
            var $element = $(element);
            var index = stars.indexOf($(element).data('id'));
            if (index > -1) {
                $(element).addClass('star-on');
            }
        });
   }

   function initialSync() {
       $.getJSON($('starred-event').data('get')).then(function(response) {
           if (response) {
               csrfToken = response.csrf_token;
               stars.concat(response.ids);
               if (csrfToken) {
                  sync();
               }
           }
       });
   }

   function sync() {
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
                  triggerClickedStars();
              }
          });
      }
   }

   function toggleArrayPresence(id) {
      var index = stars.indexOf(id);
      if (index > -1) {
         stars.splice(index, 1);
      } else {
         stars.push(id);
      }
      localStorage.setItem('stars', JSON.stringify(stars));
      sync();
   }


   $('a.star').on('click', function () {
      toggleArrayPresence($(this).data('id'));
      $(this).toggleClass('star-on');
   });

   if (from_browser) {
       stars = JSON.parse(from_browser);
       triggerClickedStars();
   }
   sync();
});
