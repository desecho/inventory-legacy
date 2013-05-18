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

function get_current_datetime() {
  var currentDate = new Date();
  var day = currentDate.getDate();
  var month = currentDate.getMonth() + 1;
  var year = currentDate.getFullYear();
  var hours = currentDate.getHours();
  var minutes = currentDate.getMinutes();
  if (minutes < 10) minutes = '0' + minutes;
  return day + '.' + month + '.' + year + ' ' + hours + ":" + minutes;
}

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
  function create_print_area() {
    var from_to_title;
    if (request_type == 1) {
      from_to_title = 'Откуда';
    } else {
      from_to_title = 'Куда';
    }
    var item_ids = get_item_ids();
    var output = '<h2 class="text-center">Заявка</h2><table class="table"><thead><tr><th>' + from_to_title + '</th><th>Наименование</th><th>Количество</th><th>Комментарий</th></tr></thead><tbody>';
    for (var i = 0, len = item_ids.length; i < len; i++) {
      var id = item_ids[i];
      output += '<tr><td>' + $('#box' + id).find(":selected").text() + '</td><td>' + $('#item_name' + id).find(":selected").text() + '</td><td>' + $('#quantity' + id).val() + '</td><td>' + $('#comment' + id).val() + '</td></tr>';
    }
    output += '</tbody></table><br><br>Дата/Время: ' + get_current_datetime() + '<br>Тип заявки: ' + request_type_text + '<br>Выписано на: ' + $('#id_person').find(":selected").text() + '<br><br>' + user + ' _______________________________<br>Гуров А. С. _______________________________';
    $('#to-print').html(output);
  }
  if (validate_form()) {
    create_print_area();
    window.print();
  }
}





