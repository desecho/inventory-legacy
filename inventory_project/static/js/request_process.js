$(function() {
  $("#request").validate();
});

function save_request() {
  function create_or_update_packet() {
    return ajax_create_or_update_packet(packet_id);
  }
  if (validate_form(true)) {
    if (create_or_update_packet()) {
      displayMessage(1, 'Форма сохранена успешно');
      return true;
    }
  }
}

function process_request() {
  if (save_request()) {
    submit_form();
  }
}

function submit_form(delete_request) {
  delete_request = typeof delete_request !== 'undefined' ? delete_request : 0;
  $('#delete').val(delete_request);  //make sure the request doesn't get deleted if validation stucks or something
  $('#request').submit();
}

function delete_request() {
  submit_form(1);
}