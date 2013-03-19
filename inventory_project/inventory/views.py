# -*- coding: utf8 -*-
import json
from django.shortcuts import redirect
from inventory.models import (Item, Box, InventoryItem, Movement, Packet,
                              PacketItem, Request, RequestType)
from inventory.forms import (ReceiptForm, InventoryReportForm,
                             MovementsReportForm, RequestAddForm,
                             RequestsListProcessedForm, Choices,
                             date_initial)
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from annoying.decorators import ajax_request, render_to

generic_permission = 'inventory.add_item'


def logout_view(request):
    logout(request)
    return redirect('/login/')


@render_to('index.html')
@login_required
def home(request, message=None, message_status=None):
    return {'message': message, 'message_status': message_status}


# Inventory START
def get_quantity_in_inventory(box, item):
        try:
            quantity = InventoryItem.objects.get(box=box, item=item).quantity
        except InventoryItem.DoesNotExist:
            quantity = 0
        return quantity


def is_enough_item_in_inventory(box, item, required_quantity):
    return get_quantity_in_inventory(box, item) >= required_quantity


def move_item(box_from, box_to, item, quantity, comment):
    def add_items_to_box_in_inventory(box, item, quantity):
        inventory, created = InventoryItem.objects.get_or_create(
            item=item, box=box, defaults={'quantity': 0})
        inventory.quantity += quantity
        inventory.save()

    def remove_items_from_box_in_inventory(box, item, quantity):
        inventory = InventoryItem.objects.get(item=item, box=box)
        inventory.quantity -= quantity
        if inventory.quantity == 0:
            inventory.delete()
        else:
            inventory.save()
    if (box_from.pk in [3, 4] or  # if receipt
       is_enough_item_in_inventory(box_from, item, quantity)):
        if box_from.pk not in [3, 4]:
            remove_items_from_box_in_inventory(box_from, item, quantity)
        if box_to.pk not in [2, 4]:
            add_items_to_box_in_inventory(box_to, item, quantity)
        Movement(box_from=box_from, box_to=box_to, item=item,
                 quantity=quantity, comment=comment).save()
        return True
# Inventory END


@render_to('receipt.html')
@permission_required(generic_permission)
@login_required
def receipt(request):
    def get_item_names_json():
        items = Item.objects.filter(deleted=False)
        items_names = []
        for item in items:
            items_names.append(item.name)
        return json.dumps(items_names)

    message = None
    form = ReceiptForm(request.POST or None)
    if form.is_valid():
        move_item(Box.objects.get(pk=3),  # receipt
                  Box.objects.get(pk=1),  # storage
                  form.cleaned_data['item'], form.cleaned_data['quantity'],
                  form.cleaned_data['comment'])
        message = 'Оформлено'
        form = ReceiptForm()
    return {'form': form,
            'items': get_item_names_json(),
            'message': message,
            'message_status': 1}


@render_to('reports/inventory.html')
@login_required
def reports_inventory(request):
    inventory = None
    def filter_results(item, person, location):
        if item:
            inventory = InventoryItem.objects.filter(item=item)
        else:
            inventory = InventoryItem.objects.all()
        if person:
            inventory = inventory.filter(box=person)
        if location:
            inventory = inventory.filter(box=location)
        return inventory

    form = InventoryReportForm(request.POST or None)
    if form.is_valid():
        inventory = filter_results(form.cleaned_data['item'],
                                   form.cleaned_data['person'],
                                   form.cleaned_data['location'])
        inventory = inventory.order_by('box__box_type', 'box__name',
                                       'item__name')
    return {'form': form, 'inventory': inventory}

@render_to('reports/inventory-storage.html')
@login_required
def reports_inventory_storage(request):
    'shows items with quantity lower or equal to minimal'
    items = []
    for item in Item.objects.filter(deleted=False):
        if (not is_enough_item_in_inventory(
           1, item, item.minimal_quantity_in_storage)):  # box - storage
            items.append((item.name, get_quantity_in_inventory(1, item),
                         item.minimal_quantity_in_storage))
    return {'items': items}


def get_date_initial():
    return [date.strftime(settings.FORMAT_DATE) for date in date_initial]


@render_to('reports/movements.html')
@login_required
def reports_movements(request):
    def filter_results(item, box, box_from, box_to, date_from, date_to):
        if item:
            movements = Movement.objects.filter(item=item)
        else:
            movements = Movement.objects.all()

        if box:
            movements_box_from = movements.filter(box_from=box)
            movements_box_to = movements.filter(box_to=box)
            movements = movements_box_from | movements_box_to
        else:
            if box_from:
                movements = movements.filter(box_from=box_from)

            if box_to:
                movements = movements.filter(box_to=box_to)
        movements = movements.filter(date__range=(date_from, date_to))
        return movements
    movements = None
    form = MovementsReportForm(request.POST or None)
    if form.is_valid():
        movements = filter_results(form.cleaned_data['item'],
                                   form.cleaned_data['box'],
                                   form.cleaned_data['box_from'],
                                   form.cleaned_data['box_to'],
                                   form.cleaned_data['date_from'],
                                   form.cleaned_data['date_to'])
        movements = movements.order_by('date', 'box_from__box_type',
                                       'box_to__box_type',
                                       'box_from__name', 'box_to__name',
                                       'item__name')
    # date_initial variable because it's more convinient for js form reset
    return {'form': form,
            'movements': movements,
            'date_initial': get_date_initial()}


class RequestData:
    def __init__(self, request_type):
        self.request_type = request_type

    def get_item_names_in_boxes_json(self):
        if self.request_type == 1:
            boxes = (Box.objects.filter(box_type=4) |  # storage
                     Box.objects.filter(box_type=6))   # locations
        else:
            boxes = Box.objects.filter(box_type=5)     # persons
        item_names_in_boxes = []
        for box in boxes:
            item_names_in_box = []
            inventory_items = InventoryItem.objects.filter(box=box)
            for inventory_item in inventory_items:
                item_names_in_box.append((inventory_item.item.pk,
                                         inventory_item.item.name))
            item_names_in_boxes.append((box.pk, item_names_in_box))
        return json.dumps(item_names_in_boxes)

    def get_choices_json(self):
        if self.request_type == 1:
            choices = Choices().storage_with_locations
        else:
            choices = Choices().expense_with_locations
        return json.dumps(choices)


@render_to('requests/add.html')
def requests_add(request, request_type):
    def add_user_to_form(form):
        form = form.save(False)
        form.user = request.user
        return form

    if request.POST:
        form = RequestAddForm(request.POST)
    else:
        form = RequestAddForm(initial={'request_type': request_type})
    if form.is_valid():
        form = add_user_to_form(form)
        form.save()
        return home(request, 'Заявка принята', 1)
    request_data = RequestData(request_type)
    return {'form': form,
            'boxes': request_data.get_choices_json(),
            'item_names_in_boxes': request_data.get_item_names_in_boxes_json(),
            'request_type': RequestType.objects.get(pk=request_type)}


@login_required
def requests_add_receipt(request):
    return requests_add(request, 1)


@login_required
def requests_add_expense(request):
    return requests_add(request, 2)


@ajax_request
def ajax_check_availability_receipt(request):
    def sum_duplicates(items):
        output = {}
        for item in items:
            if (item[0], item[1]) in output:
                output[(item[0], item[1])] += int(item[2])
            else:
                output[(item[0], item[1])] = int(item[2])
        return output

    def is_enough_items_in_inventory(items_request):
        message = None
        status = True
        for item_request in items_request:
            box = Box.objects.get(pk=item_request[0])
            item = Item.objects.get(pk=item_request[1])
            quantity = items_request[item_request]
            if not is_enough_item_in_inventory(box, item, quantity):
                message = (u'Недостаточно "%s" в "%s" (необходимо %d, в наличие %d)' %
                    (item.name, box.name, quantity, get_quantity_in_inventory(box, item)))
                status = False
                break
        return (status, message)

    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'item_data' in POST:
            items = sum_duplicates(json.loads(POST.get('item_data')))
            status, message = is_enough_items_in_inventory(items)
            return {'status': status, 'message': message}


@ajax_request
def ajax_check_availability_expense(request):
    def sum_duplicates(items_request):
        output = {}
        for item_request in items_request:
            if item_request[1] in output:
                output[item_request[1]] += int(item_request[2])
            else:
                output[item_request[1]] = int(item_request[2])
        return output

    def required_comments_present(items):
        for item in items:
            if item[0] == '2' and not item[3]:
                return False
        return True

    def is_enough_items_in_inventory(items_request, box):
        message = None
        status = True
        for item_request in items_request:
            item = Item.objects.get(pk=item_request)
            quantity = items_request[item_request]
            if not is_enough_item_in_inventory(box, item, quantity):
                message = (u'Недостаточно "%s" у "%s" (необходимо %d, имеется %d)' %
                    (item.name, box.name, quantity, get_quantity_in_inventory(box, item)))
                status = False
                break
        return (status, message)

    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'item_data' in POST and 'person' in POST:
            items_request = json.loads(POST.get('item_data'))
            if required_comments_present(items_request):
                items = sum_duplicates(items_request)
                person = Box.objects.get(pk=POST.get('person'))
                status, message = is_enough_items_in_inventory(items, person)
            else:
                message = u'Отсутствует необходимый комментарий'
                status = False
            return {'status': status, 'message': message}


@ajax_request
def ajax_create_or_update_packet(request):
    def create_packet():
        packet = Packet()
        packet.save()
        return packet

    def save_packet_items(items_request, packet):
        for item_request in items_request:
            packet_item = PacketItem(packet=packet,
                                     box=Box.objects.get(pk=item_request[0]),
                                     item=Item.objects.get(pk=item_request[1]),
                                     quantity=int(item_request[2]),
                                     comment=item_request[3])
            packet_item.save()

    def clear_packet_items(packet):
        PacketItem.objects.filter(packet=packet).delete()

    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'item_data' in POST:
            if 'packet_id' in POST:
                packet = Packet.objects.get(pk=POST.get('packet_id'))
                clear_packet_items(packet)
            else:
                packet = create_packet()
            save_packet_items(json.loads(POST.get('item_data')), packet)
            return {'packet_id': packet.pk}


@render_to('requests/list.html')
@permission_required(generic_permission)
@login_required
def requests_list(request, message=None, message_status=None):
    return {'requests': Request.objects.filter(processed=0),
            'message': message,
            'message_status': message_status}

@render_to('requests/process.html')
@permission_required(generic_permission)
@login_required
def requests_process(request, id):
    def get_packet_items_json():
        packet_items = PacketItem.objects.filter(packet=packet)
        output = []
        for item in packet_items:
            output.append((item.box.pk, item.item.pk, item.quantity, item.comment))
        return json.dumps(output)

    def delete_request_with_its_packet():
        packet.delete()
        request_item.delete()

    def process_request():
        def mark_request_as_processed():
            request_item.processed = True
            request_item.save()

        def process_movements():
            packet_items = PacketItem.objects.filter(packet=packet)
            for item in packet_items:
                if request_type.pk == 1:
                    box_from = item.box
                    box_to = person
                else:
                    box_from = person
                    box_to = item.box
                '''
                    Not required to check if the move has been successful
                    because it is supposed to be always successful since only
                    one administrator is going to work with this. If multiple
                    admins suddenly. This issue has to be addressed.
                '''
                move_item(box_from, box_to, item.item, item.quantity, item.comment)
        process_movements()
        mark_request_as_processed()

    request_item = Request.objects.get(pk=id)
    request_type = request_item.request_type
    person = request_item.person
    packet = request_item.packet
    if request.method == 'POST':
		delete = int(request.POST.get('delete'))
		if delete:
			delete_request_with_its_packet()
			return requests_list(request, 'Заявка удалена', 1)
		else:
			process_request()
			return requests_list(request, 'Заявка обработана', 1)
    request_data = RequestData(request_type.pk)
    return {'boxes': request_data.get_choices_json(),
            'item_names_in_boxes': request_data.get_item_names_in_boxes_json(),
            'request_type': request_type,
            'person': person,
            'packet_id': packet.pk,
            'packet_items': get_packet_items_json()}


@render_to('stocktaking/list.html')
@login_required
@permission_required(generic_permission)
def stocktaking_list(request):
    boxes = Box.objects.exclude(pk=2).exclude(pk=3).exclude(pk=4).exclude(deleted=True)
    return {'boxes': boxes}


@render_to('stocktaking/process.html')
@permission_required(generic_permission)
@login_required
def stocktaking_process(request, box_id):
    def get_items_in_box():
        items = InventoryItem.objects.filter(box=box_id).order_by('item__name')
        output = []
        for item in items:
            output.append((item.item.pk, item.quantity))
        return output

    def get_item_names_json():
        items = Item.objects.filter(deleted=False)
        items_names = []
        for item in items:
            items_names.append((item.pk, item.name))
        return json.dumps(items_names)

    def process_stocktaking(new_item_data):
        def get_differences_between_new_and_old_data():
            def get_items_in_box():
                items = InventoryItem.objects.filter(box=box_id)
                output = {}
                for item in items:
                    output[str(item.item.pk)] = item.quantity
                return output
            items_in_box = get_items_in_box()
            differences = []
            for item in items_in_box:
                if item not in new_item_data:
                    new_item_data[item] = (0, '')
                new_item_quantity = new_item_data[item][0]
                new_item_comment = new_item_data[item][1]
                old_item_quantity = items_in_box[item]
                if new_item_quantity != old_item_quantity:
                    if new_item_quantity > old_item_quantity:
                        action = 1   # means add
                    else:
                        action = 0   # means remove
                    value = abs(new_item_quantity - old_item_quantity)
                    differences.append((item, action, value, new_item_comment))
            for item in new_item_data:
                if item not in items_in_box:
                    differences.append((item, 1, new_item_data[item][0], new_item_data[item][1]))
            return differences

        def process(differences):
            stocktaking_box = Box.objects.get(pk=4)
            box = Box.objects.get(pk=box_id)
            for difference in differences:
                item = Item.objects.get(pk=difference[0])
                quantity = difference[2]
                comment = difference[3]
                if difference[1]:            # action
                    box_from = stocktaking_box
                    box_to = box
                else:
                    box_from = box
                    box_to = stocktaking_box
                move_item(box_from, box_to, item, quantity, comment)

        process(get_differences_between_new_and_old_data())
    if request.method == 'POST':
        POST = request.POST
        if 'item_data' in POST:
            process_stocktaking(json.loads(POST.get('item_data')))
            return home(request, 'Инвентаризация проведена', 1)

    return {'items': json.dumps(get_items_in_box()),
            'box': Box.objects.get(pk=box_id).name,
            'item_names': get_item_names_json()}


@render_to('requests/list_processed.html')
@login_required
def requests_list_processed(request):
    def get_items(person, date_from, date_to):
        items = []
        for request in Request.objects.filter(person=person, processed=1, date__range=(date_from, date_to)):
            packet_items = PacketItem.objects.filter(packet=request.packet)
            for packet_item in packet_items:
                items.append({'date': request.date, 'item': packet_item})
        return items
    items = None
    form = RequestsListProcessedForm(request.POST or None)
    if form.is_valid():
        person = form.cleaned_data['person']
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']
        items = get_items(person, date_from, date_to)
    # date_initial variable because it's more convinient for js form reset
    return {'form': form, 'items': items, 'date_initial': get_date_initial()}
