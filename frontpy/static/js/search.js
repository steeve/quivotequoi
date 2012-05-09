$(document).ready(function (){
  $("#search").bind("propertychange input paste", function() {
    $.get("/deputy_search", {"q": $(this).val()}, function(data) {
      $("#results").html(data);
    });
  });
});
