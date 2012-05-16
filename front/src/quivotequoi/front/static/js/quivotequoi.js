$(document).ready(function (){
  $("#search").typeahead({
    source: function(typeahead, query) {
      $.get("/deputes/search", {"q": query}, function(data) {
        typeahead.process(data);
      }, "json");
    },
    onselect: function (obj) {
      window.location = "/deputes/" + obj["uuid"];
    },
    property: "name"
  });
});

$(document).ready(function () {
  if (window.location.hash) {
    $("#more_" + window.location.hash.replace("#", "")).collapse('show');
  }
});


$(document).ready(function () {
  $(".scrutiny_link").each(function (index, Element) {
    $(Element).click(function (eventObject) {
      var scrollmem = $(window).scrollTop();
      window.location.hash = $(this).attr('name');
      $(window).scrollTop(scrollmem);
    });
  });
});
