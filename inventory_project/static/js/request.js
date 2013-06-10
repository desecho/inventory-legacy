jQuery.validator.setDefaults({success: "valid"});
jQuery.validator.addClassRules("quantity", {
  required: true,
  digits: true,
  min: 1
});
var item_id = -1;

function remove_item(id) {
  $('#item' + id).remove();
}

function get_item_ids() {
  var item_ids = [];
  $('.item').each(function() {
    item_ids.push($(this).attr('data-id'));
  });
  return item_ids;
}

function get_item_data() {
  var output = [];
  var item_ids = get_item_ids();
  for (var i = 0, len = item_ids.length; i < len; i++) {
    var id = item_ids[i];
    output.push([$('#box' + id).val(), $('#item_name' + id).val(), $('#quantity' + id).val(), $('#comment' + id).val()]);
  }
  return output;
}

function update_select_items(id, box_id) {
  var output = '<option value="">---------</option>';
  for (var i = 0, len = item_names_in_boxes.length; i < len; i++) {
    if (item_names_in_boxes[i][0] == box_id) {
      var item_names = item_names_in_boxes[i][1];
      for (i = 0, len = item_names.length; i < len; i++) {
        output += '<option value="' + item_names[i][0] + '">' + item_names[i][1] + '</option>';
      }
      break;
    }
  }
  $('#item_name' + id).html(output);
  $('#item_name' + id).select2();
}

function add_item(no_link) {
  function create_select_boxes() {
    var output = '<select class="box-select" id="box' + item_id + '">';
    for (var i = 0, len = boxes.length; i < len; i++) {
        output += '<option value="' + boxes[i][0] + '">' + boxes[i][1] + '</option>';
      }
    output += '</select>';
    return output;
  }

  function create_select_items() {
    return '<select id="item_name' + item_id + '" name="item_name' + item_id + '" class="required item-select"></select>';
  }

  item_id++;
  no_link = typeof no_link !== 'undefined' ? no_link : false;
  var link = '';
  if (!no_link) {
    link = ' <a href="#" onclick="remove_item(\'' + item_id + '\')"><i class="icon-minus-sign"></i></a>';
  }
  var item_input = '<div class="item" data-id="' + item_id + '" id="item' + item_id + '">' + create_select_boxes() + create_select_items() + ' <input type="text" name="quantity' + item_id + '" id="quantity' + item_id + '"  class="quantity" placeholder="Количество"/> <input type="text" name="comment' + item_id + '" id="comment' + item_id + '" placeholder="Комментарий"/>' + link + '<br></div>';
  $('#add_item').before(item_input);
  $('#box' + item_id).select2();
  if (request_type == 1) {
    update_select_items(item_id, 1); //set initial options for newly created select
    $('#box' + item_id).attr('onchange', 'update_select_items(' + item_id + ', this.value);');
  } else {
    update_select_items(item_id, person_id); //set initial options for newly created select
  }
}

function check_form(is_process_form) {
  is_process_form = typeof is_process_form !== 'undefined' ? is_process_form : false;
  if (validate_form(is_process_form)) {
    displayMessage(1, 'Форма заполнена верно');
  }
}

function validate_form(is_process_form){
  is_process_form = typeof is_process_form !== 'undefined' ? is_process_form : false;
  function ajax_check_availability() {
    availability = false;
    $.ajax({
      type: 'POST',
      url: '/requests/check-availability/' + request_type + '/',
      data: {'item_data': array2json(get_item_data()), 'person': person_id, 'is_process_form': is_process_form},
      success:  function(data) {
                  if (data.status) {
                    availability = true;
                  } else {
                    displayMessage(0, data.message);
                  }
                },
      async: false
    }).error(function() {
        displayMessage(0, 'Ошибка проверки данных');
    });
    return availability;
  }

  function set_required_comments_for_expense() {
    var item_ids = get_item_ids();
    for (var i = 0, len = item_ids.length; i < len; i++) {
      var id = item_ids[i];
      if ($('#box' + id).val() == 2) {
        $('#comment' + id).addClass('required');
      } else {
        $('#comment' + id).removeClass('required');
      }
    }
  }

  if (request_type == 2) {
    set_required_comments_for_expense();
  }
  return $("#request").valid() && ajax_check_availability();
}

function ajax_create_or_update_packet(packet_id) {
  packet_id = typeof packet_id !== 'undefined' ? packet_id : false;
  var new_packet_id;
  var data = {'item_data': array2json(get_item_data())};
  if (packet_id) {
    jQuery.extend(data, {'packet_id': packet_id});
  }

  $.ajax({
    type: 'POST',
    url: '/requests/create-or-update-packet/',
    data: data,
    success: function(data) {
                              new_packet_id = data.packet_id;
                            },
    async: false
  }).error(function() {
      displayMessage(0, 'Ошибка создания пакета');
  });
  return new_packet_id;
}

function create_print_area(request_person) {
  function get_current_datetime() {
    var current_date = new Date();
    var day = current_date.getDate();
    var month = current_date.getMonth() + 1;
    var year = current_date.getFullYear();
    var hours = current_date.getHours();
    var minutes = current_date.getMinutes();
    if (minutes < 10) {
      minutes = '0' + minutes;
    }
    return day + '.' + month + '.' + year + ' ' + hours + ':' + minutes;
  }
  date = typeof date !== 'undefined' ? date : get_current_datetime();
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
  output += '</tbody></table><br><br>Дата/Время: ' + date + '<br>Тип заявки: ' + request_type_text + '<br>Лицо: ' + request_person + '<br><br>' + user + ' _______________________________<br>Гуров А. С. _______________________________';
  $('#to-print').html(output);
}