$(function() {
  $.datepicker.regional['ru'] = {
    closeText: 'Закрыть',
    prevText: '<Пред',
    nextText: 'След>',
    currentText: 'Сегодня',
    monthNames: ['Январь','Февраль','Март','Апрель','Май','Июнь',
    'Июль','Август','Сентябрь','Октябрь','Ноябрь','Декабрь'],
    monthNamesShort: ['Янв','Фев','Мар','Апр','Май','Июн',
    'Июл','Авг','Сен','Окт','Ноя','Дек'],
    dayNames: ['воскресенье','понедельник','вторник','среда','четверг','пятница','суббота'],
    dayNamesShort: ['вск','пнд','втр','срд','чтв','птн','сбт'],
    dayNamesMin: ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'],
    weekHeader: 'Не',
    dateFormat: 'dd.mm.yy',
    firstDay: 1,
    isRTL: false,
    showMonthAfterYear: false,
    yearSuffix: ''
  };
  $.datepicker.setDefaults($.datepicker.regional['ru']);
  $("#id_date_from").datepicker({
    onSelect: function( selectedDate ) {
      $("#id_date_to").datepicker("option", "minDate", selectedDate);
    }
  });
  $("#id_date_to").datepicker({
    onSelect: function( selectedDate ) {
      $("#id_date_from").datepicker("option", "maxDate", selectedDate);
    }
  });
});