jQuery.validator.setDefaults({success: "valid"});
jQuery.validator.addClassRules("quantity", {
  required: true,
  digits: true,
  min: 0
});
var item_id = -1;

function get_item_data() {
  var output = {};
  var item_ids = get_item_ids();
  for (var i = 0, len = item_ids.length; i < len; i++) {
    var id = item_ids[i];
    output[parseInt($('#item_name' + id).val(), 10)] = [parseInt($('#quantity' + id).val(), 10), $('#comment' + id).val()];
  }
  return output;
}

function remove_item(id) {
  $('#item' + id).remove();
}

function add_item() {
  function create_select_items() {
    var output = '<select name="item_name' + item_id + '" id="item_name' + item_id + '" class="required" onchange="onchange_item_names(' + item_id + ')"><option value="">---------</option>';
    for (var i = 0, len = item_names.length; i < len; i++) {
      output += '<option value="' + item_names[i][0] + '">' + item_names[i][1] + '</option>';
    }
    output += '</select>';
    return output;
  }
  item_id++;
  var link = ' <a href="#" onclick="remove_item(\'' + item_id + '\')"><i class="icon-minus-sign"></i></a>';
  var item_input = '<div class="item" data-id="' + item_id + '" id="item' + item_id + '"> <span id="item_name_text' + item_id + '"></span> ' + create_select_items() + ' <input type="text" disabled id="quantity_initial' + item_id + '" /> <input type="text" name="quantity' + item_id + '" id="quantity' + item_id + '"  class="quantity" placeholder="Количество"/> <input type="text" name="comment' + item_id + '" id="comment' + item_id + '" placeholder="Комментарий"/>' + link + '<br></div>';
  $('#add_item').before(item_input);
}

function get_item_ids() {
  var item_ids = [];
  $('.item').each(function() {
    item_ids.push($(this).attr('data-id'));
  });
  return item_ids;
}

function onchange_item_names(id) {
  check_if_item_name_in_list(id);
  //$('#item_name_text' + id).html($('#item_name' + id).children(':selected').text());
}

function check_if_item_name_in_list(id) {
  function check_if_duplicates_exist(){
    var output = [];
    var item_ids = get_item_ids();
    for (var i = 0, len = item_ids.length; i < len; i++) {
      var item_id = item_ids[i];
      var value = $('#item_name' + item_id).val();
      if (jQuery.inArray(value, output) != -1 && value !== '') {
        return true;
      }
      output.push(value);
    }
  }
  if (check_if_duplicates_exist()) {
    displayMessage(0, 'Такое наименование уже присутствует в списке.');
    $('#item_name' + id).val('');
  }
}

$(function() {
  $("#stocktaking").validate();
  for (var i = 0, len = items.length; i < len; i++) {
    var item = items[i];
    add_item();
    $('#item_name' + i).val(item[0]);
    $('#quantity_initial' + i).val(item[1]);
    $('#quantity' + i).val(item[1]);
    $('#comment' + i).val(item[2]);
  }
});


function check_form() {
  if (validate_form()) {
    displayMessage(1, 'Заполнено верно');
  }
}

function validate_form(){
  return $("#stocktaking").valid();
}

function process() {
  if (validate_form()) {
    $('#item_data').val(JSON.stringify(get_item_data()));
    $('#stocktaking').submit();
  }
}