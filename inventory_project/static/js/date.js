$(function() {
  $("#id_date_from").datepicker({
    onSelect: function( selectedDate ) {
      $("#id_date_to").datepicker("option", "minDate", selectedDate);
    }
  });
  $("#id_date_to").datepicker({
    onSelect: function( selectedDate ) {
      $("#id_date_from").datepicker("option", "maxDate", selectedDate);
    }
  });
});