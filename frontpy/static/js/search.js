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
