$(function() {
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