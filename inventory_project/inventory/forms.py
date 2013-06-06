# -*- coding: utf8 -*-
from django import forms
from datetime import timedelta, date, datetime
from django.conf import settings
from inventory.models import Item, Box, Request, InventoryItem
from django.contrib.auth.models import User

dates_initial = (date.today() - timedelta(days=30), date.today())
dates_initial_stats = (datetime.strptime(settings.START_DATE, settings.FORMAT_DATE), date.today())
default_value = [('', '-' * 9)]


def convert_date_to_datetime(date):
    'convert date to datetime to show last day results'
    return datetime(date.year, date.month, date.day, 23, 59, 59)


class Choices:
    def __init__(self, hide_deleted=True):
        self.hide_deleted = hide_deleted
        self.items = self.create_items_list()
        self.persons = self.create_box_list(5)
        self.storage = self.create_box_list(1)
        self.locations = self.create_box_list(6)
        self.correction = self.create_box_list(4)
        self.expense = self.create_box_list(2)
        self.receipt = self.create_box_list(3)
        self.storage_with_locations = self.storage + self.locations
        self.expense_and_storage_with_locations = self.expense + self.storage + self.locations  # for views
        self.basic_set = self.storage + self.persons + self.locations + self.correction
        self.boxes_from = self.receipt + self.basic_set
        self.boxes_to = self.expense + self.basic_set
        self.boxes = self.receipt + self.expense + self.basic_set
        self.persons_with_no_default_value = default_value + self.persons

    def create_list(self, objects):
        choices = []
        for object in objects:
            choices.append((object.pk, object.name))
        return choices

    def create_items_list(self):
        items = Item.objects.all()
        if self.hide_deleted:
            items = items.exclude(deleted=True)
        items = items.order_by('name')
        return self.create_list(items)

    def create_box_list(self, id):
        boxes = Box.objects.filter(box_type=id)
        if self.hide_deleted:
            boxes = boxes.exclude(deleted=True)
        boxes = boxes.order_by('name')
        return self.create_list(boxes)

    def output(self, list):
        return [(0, '')] + list

    def output_items(self):
        return self.output(self.items)

    def output_persons(self):
        return self.output(self.persons)

    def output_storage_with_locations(self):
        return self.output(self.storage_with_locations)

    def output_boxes_from(self):
        return self.output(self.boxes_from)

    def output_boxes_to(self):
        return self.output(self.boxes_to)

    def output_boxes(self):
        return self.output(self.boxes)


class RequestAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RequestAddForm, self).__init__(*args, **kwargs)
        self.fields['person'].choices = Choices().persons_with_no_default_value

    person = forms.ChoiceField(label='Лицо')

    class Meta:
        model = Request
        exclude = ('user', 'date', 'processed')
        widgets = {
            'request_type': forms.HiddenInput(),
            'packet': forms.HiddenInput(),
        }

    def clean_person(self):
        return Box.objects.get(pk=self.cleaned_data['person'])


class ReceiptForm(forms.ModelForm):
    item = forms.CharField(label='Наименование',
                           widget=forms.TextInput(attrs={'required': '', 'autofocus': ''}))
    comment = forms.CharField(label='Комментарий', required=False)

    def clean_item(self):
        # Add a new item if it's not in the database yet.
        item, _ = Item.objects.get_or_create(
            name=self.cleaned_data['item'])
        return item

    def clean_quantity(self):
        if self.cleaned_data['quantity'] < 1:
            raise forms.ValidationError(
                'Введите количество большее или равное 1')
        return self.cleaned_data['quantity']

    class Meta:
        model = InventoryItem
        exclude = ('box',)
        widgets = {
            'quantity': forms.TextInput(attrs={'required': '',
                                               'pattern': '\d+',
                                               'title': 'число'}),
        }


class LocationForm(forms.ModelForm):
    name = forms.CharField(label='Адрес',
                           widget=forms.TextInput(attrs={'required': '', 'autofocus': ''}))

    def clean_name(self):
        return self.cleaned_data['name'].strip()

    class Meta:
        model = Box
        exclude = ('box_type', 'deleted')


class InventoryReportForm(forms.Form):
    def __init__(self, *args, **kwargs):
            super(InventoryReportForm, self).__init__(*args, **kwargs)
            choices = Choices()
            self.fields['item'].choices = choices.output_items()
            self.fields['person'].choices = choices.output_persons()
            self.fields['location'].choices = choices.output_storage_with_locations()

    item = forms.ChoiceField(label='Наименование', required=False)
    person = forms.ChoiceField(label='Лицо', required=False)
    location = forms.ChoiceField(label='Узел', required=False)

    def clean_item(self):
        if not int(self.cleaned_data['item']):
            return
        return Item.objects.get(pk=self.cleaned_data['item'])

    def clean_person(self):
        if not int(self.cleaned_data['person']):
            return
        return Box.objects.get(pk=self.cleaned_data['person'])

    def clean_location(self):
        if not int(self.cleaned_data['location']):
            return
        return Box.objects.get(pk=self.cleaned_data['location'])


def create_form_date_fields(dates):
    def create_form_date_field(label, initial_date):
        widget_attrs = {'required': '', 'pattern': '^\d{2}\.\d{2}\.\d{4}$'}
        return forms.DateField(label=label,
                               initial=initial_date,
                               widget=forms.DateInput(attrs=widget_attrs, format=settings.FORMAT_DATE),
                               input_formats=(settings.FORMAT_DATE,))
    date_from = create_form_date_field('От', dates[0])
    date_to = create_form_date_field('До', dates[1])
    return (date_from, date_to)


class StatsReportForm(forms.Form):
    def __init__(self, *args, **kwargs):
            super(StatsReportForm, self).__init__(*args, **kwargs)
            users = User.objects.all()
            users = [(user.pk, user.get_full_name()) for user in users]
            self.fields['user'].choices = default_value + users

    user = forms.ChoiceField(label='Пользователь', required=False)
    period = forms.ChoiceField(label='Период', required=True, choices=[
        (7, 'неделя'),
        (30, 'месяц'),
        (180, 'полгода')]
    )
    date_from, date_to = create_form_date_fields(dates_initial_stats)

    def clean_user(self):
        if not self.cleaned_data['user']:
            return
        return User.objects.get(pk=self.cleaned_data['user'])

    def clean_period(self):
        return int(self.cleaned_data['period'])


class MovementsReportForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MovementsReportForm, self).__init__(*args, **kwargs)
        choices = Choices(False)
        self.fields['box'].choices = choices.output_boxes()
        self.fields['box_from'].choices = choices.output_boxes_from()
        self.fields['box_to'].choices = choices.output_boxes_to()
        self.fields['item'].choices = choices.output_items()

    box = forms.ChoiceField(label='Коробка', required=False)
    box_from = forms.ChoiceField(label='Откуда', required=False)
    box_to = forms.ChoiceField(label='Куда', required=False)
    item = forms.ChoiceField(label='Наименование', required=False)
    date_from, date_to = create_form_date_fields(dates_initial)

    def clean_item(self):
        if not int(self.cleaned_data['item']):
            return
        return Item.objects.get(pk=self.cleaned_data['item'])

    def clean_box_from(self):
        if not int(self.cleaned_data['box_from']):
            return
        return Box.objects.get(pk=self.cleaned_data['box_from'])

    def clean_box_to(self):
        if not int(self.cleaned_data['box_to']):
            return
        return Box.objects.get(pk=self.cleaned_data['box_to'])

    def clean_box(self):
        if not int(self.cleaned_data['box']):
            return
        return Box.objects.get(pk=self.cleaned_data['box'])

    def clean_date_to(self):
        date_to = self.cleaned_data['date_to']
        return convert_date_to_datetime(date_to)


class RequestsListProcessedForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(RequestsListProcessedForm, self).__init__(*args, **kwargs)
        self.fields['person'].choices = Choices().persons_with_no_default_value

    person = forms.ChoiceField(label='Лицо', widget=forms.Select(attrs={'required': ''}))
    date_from, date_to = create_form_date_fields(dates_initial)

    def clean_person(self):
        if not int(self.cleaned_data['person']):
            return
        return Box.objects.get(pk=self.cleaned_data['person'])

    def clean_date_to(self):
        date_to = self.cleaned_data['date_to']
        return convert_date_to_datetime(date_to)
