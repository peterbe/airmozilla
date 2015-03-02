$(function() {
    var stars = [],
    csrf_token,
    isLoggedIn,
    from_browser = localStorage.getItem('stars');


   function triggerClickedStars() {
        $('a.star').each(function(i, element) {
            var index = stars.indexOf($(element).data('id'))
            if (index > -1) {
                $(element).addClass('star-on')
            }
            else {
                $(element).removeClass('star-on')
            }
        });
   }

   function initialSync() {
       $.getJSON('/starred/sync/').then(function(response) {
           if (response) {
               csrf_token = response.csrf_token;
               isLoggedIn = response.isLoggedIn;
               stars.concat(response.ids);
               if (csrf_token)
                  sync();
           }
       });
   }

   function sync() {
      if (!csrf_token)
          return initialSync();
      if (!isLoggedIn)
          return;

// Can also set this to $.param({'ids': stars, 'csrfmiddlewaretoken': csrf_token}, true).then(
// and remove the square brackets from starred/views.py line 30
// Or manually encode and decode JSON. See http://api.jquery.com/jQuery.param/
       $.post('/starred/sync/', {'ids': stars, 'csrfmiddlewaretoken': csrf_token}).then(
               function(response) {
                   if (response) {
                       csrf_token = response.csrf_token;
                       isLoggedIn = response.isLoggedIn;
                       stars = response.ids;
                       localStorage.setItem('stars', JSON.stringify(stars));
                       triggerClickedStars();
                   }
               });
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
