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

function add_location(){
  function add_location_to_boxes(id, name) {
    $('.box-select').each(function() {
      var option = '<option value="' + id + '">' + name + '</option>';
      $(this).select2('destroy');
      $(this).append(option);
    });
    $('.box-select').each(function() {
      $(this).select2();
    });
    var new_location = [id, name];
    boxes.push(new_location);
  }
  var location = $('#location').val();
  $.post('/ajax-add-location/', {location: location}, function(data) {
    add_location_to_boxes(data.id, data.location);
    displayMessage(1, 'Узел успешно добавлен');
  }).error(function() {
    displayMessage(0, 'Ошибка добавления узла');
  });
}