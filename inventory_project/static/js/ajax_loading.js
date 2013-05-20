$(function() {
  $(document).ajaxStart(function(){
    $('#loading').show();
    $('.btn').attr('disabled', 'disabled');
  });

  $(document).ajaxStop(function(){
    $('#loading').hide();
    $('.btn').removeAttr('disabled');
  });
});