$(function() {
  $("#request").validate();
  for (var i = 0, len = packet_items.length; i < len; i++) {
    var item = packet_items[i];
    var no_link = false;
    if (i === 0) {
      no_link = true;
    }
    add_item(no_link);
    $('#box' + i).val(item[0]);
    $('#item_name' + i).val(item[1]);
    $('#item_name' + i).select2();
    $('#quantity' + i).val(item[2]);
    $('#comment' + i).val(item[3]);
  }
});

function save_request() {
  function create_or_update_packet() {
    return ajax_create_or_update_packet(packet_id);
  }
  if (validate_form()) {
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