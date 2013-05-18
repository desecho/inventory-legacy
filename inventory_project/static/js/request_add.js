var person_id;

$(function() {
  $("#request").validate({rules: {person:'required'}});
  if (request_type == 1) {
    add_item(true);
  } else {
    $('#id_person').change(function() {
      $('#id_person').attr('disabled', '');
      person_id = $('#id_person').val();
      add_item(true);
      $('#add_item').show();
    });
    $('#add_item').hide();
  }
});

function submit_form() {
  function create_packet() {
    var packet_id = ajax_create_or_update_packet();
    if (packet_id) {
      $('#id_packet').val(packet_id);
      return true;
    }
  }
  if (validate_form()) {
    if (create_packet()) {
      if (request_type == 2) {
        $('#id_person').removeAttr('disabled');
      }
      $('#request').submit();
    }
  }
}

function print_request() {
  if (validate_form()) {
    create_print_area();
    window.print();
  }
}