# -*- coding: utf8 -*-
from django import forms
from datetime import timedelta, date
from django.conf import settings
from inventory.models import Item, Box, Request, InventoryItem

date_initial = (date.today() - timedelta(days=30), date.today())

class Choices:
    def __init__(self, hide_deleted=True):
        self.hide_deleted = hide_deleted
        self.items = self.create_items_list()
        self.persons = self.create_box_list(5)
        self.storage = self.create_box_list(4)
        self.locations = self.create_box_list(6)
        self.correction = self.create_box_list(3)
        self.expense = self.create_box_list(2)
        self.receipt = self.create_box_list(1)
        self.storage_with_locations = self.storage + self.locations
        self.expense_with_locations = self.expense + self.locations  # for views
        self.basic_set = self.storage + self.persons + self.locations + self.correction
        self.boxes_from = self.receipt + self.basic_set
        self.boxes_to = self.expense + self.basic_set
        self.boxes = self.receipt + self.expense + self.basic_set
        default_value = [('', '-' * 9)]
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
        return self.create_list(items)

    def create_box_list(self, id):
        boxes = Box.objects.filter(box_type=id)
        if self.hide_deleted:
            boxes = boxes.exclude(deleted=True)
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
    person = forms.ChoiceField(label='Лицо',
                             choices=Choices().persons_with_no_default_value)

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
        item, created = Item.objects.get_or_create(
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


class InventoryReportForm(forms.Form):
    choices = Choices()
    item = forms.ChoiceField(label='Наименование', choices=choices.output_items(), required=False)
    person = forms.ChoiceField(label='Лицо', choices=choices.output_persons(), required=False)
    location = forms.ChoiceField(label='Узел', choices=choices.output_storage_with_locations(), required=False)

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


def create_form_date_field(date_type):
    if date_type == 'from':
        label = 'От'
        initial_date = date_initial[0]
    else:
        label = 'До'
        initial_date = date_initial[1]
    return forms.DateField(label=label, initial=initial_date, widget=forms.DateInput(attrs={'required': '', 'pattern': '^\d{2}\.\d{2}\.\d{4}$'}, format=settings.FORMAT_DATE), input_formats=(settings.FORMAT_DATE,))


class MovementsReportForm(forms.Form):
    choices = Choices(False)
    box = forms.ChoiceField(label='Коробка', choices=choices.output_boxes(), required=False)
    box_from = forms.ChoiceField(label='Откуда', choices=choices.output_boxes_from(), required=False)
    box_to = forms.ChoiceField(label='Куда', choices=choices.output_boxes_to(), required=False)
    item = forms.ChoiceField(label='Наименование', choices=choices.output_items(), required=False)
    date_from = create_form_date_field('from')
    date_to = create_form_date_field('to')

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


class RequestsListProcessedForm(forms.Form):
    person = forms.ChoiceField(label='Лицо',
                             choices=Choices().persons_with_no_default_value,
                             widget=forms.Select(attrs={'required': ''}))
    date_from = create_form_date_field('from')
    date_to = create_form_date_field('to')

    def clean_person(self):
        if not int(self.cleaned_data['person']):
            return
        return Box.objects.get(pk=self.cleaned_data['person'])
