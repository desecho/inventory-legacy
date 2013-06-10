$(function() {
  $('input,select').not('.btn').attr('disabled', 'disabled');
});

function print_request() {
  create_print_area(person_name);
  window.print();
}