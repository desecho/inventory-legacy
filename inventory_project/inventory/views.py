# -*- coding: utf8 -*-
import json
import chromelogger as console
import PyICU
from operator import itemgetter
from django.shortcuts import redirect
from inventory.models import (Item, Box, InventoryItem, Movement, Packet,
                              PacketItem, Request, RequestType)
from inventory.forms import (ReceiptForm, InventoryReportForm,
                             MovementsReportForm, RequestAddForm,
                             RequestsListProcessedForm, LocationForm,
                             StatsReportForm, Choices, load_dates_initial,
                             load_dates_initial_stats, convert_date_to_datetime)
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
    """
    Args:
        box: Box
        item: Item

    Returns:
        int
    """
    try:
        quantity = InventoryItem.objects.get(box=box, item=item).quantity
    except InventoryItem.DoesNotExist:
        quantity = 0
    return quantity


def is_enough_item_in_inventory(box, item, required_quantity):
    """
    Args:
        box: Box
        item: Item
        required_quantity: int

    Returns:
        bool
    """
    return get_quantity_in_inventory(box, item) >= required_quantity


def move_item(box_from, box_to, item, quantity, comment):
    """
    Args:
        box_from, box_to: Box
        item: Item
        quantity: int
        comment: string
    """
    def is_box_from_type_receipt_or_stocktaking():
        'Returns: bool'
        return box_from.box_type.pk in [3, 4]

    def add_items_to_box_in_inventory(box):
        'Args: box: Box'
        inventory, _ = InventoryItem.objects.get_or_create(
            item=item,
            box=box,
            defaults={'quantity': 0})
        inventory.quantity += quantity
        inventory.save()

    def remove_items_from_box_in_inventory(box):
        'Args: box: Box'
        inventory = InventoryItem.objects.get(item=item, box=box)
        inventory.quantity -= quantity
        if inventory.quantity == 0:
            inventory.delete()
        else:
            inventory.save()

    if is_box_from_type_receipt_or_stocktaking() or is_enough_item_in_inventory(box_from, item, quantity):
        if not is_box_from_type_receipt_or_stocktaking():
            remove_items_from_box_in_inventory(box_from)
        if box_to.box_type.pk not in [2, 4]:  # expense or stocktaking
            add_items_to_box_in_inventory(box_to)
        Movement(box_from=box_from, box_to=box_to, item=item,
                 quantity=quantity, comment=comment).save()
# Inventory END


@render_to('receipt.html')
@permission_required(generic_permission)
@login_required
def receipt(request):
    def get_item_names_json():
        """
        Returns: string json
            list of strings - item names
        """
        items = Item.objects.filter(deleted=False)
        items_names = [item.name for item in items]
        return json.dumps(items_names)

    message = None
    form = ReceiptForm(request.POST or None)
    if form.is_valid():
        move_item(Box.objects.get(pk=3),  # receipt
                  Box.objects.get(pk=1),  # storage
                  form.cleaned_data['item'],
                  form.cleaned_data['quantity'],
                  form.cleaned_data['comment'])
        message = 'Приход на склад оформлен'
        form = ReceiptForm()
    return {'form': form,
            'items': get_item_names_json(),
            'message': message,
            'message_status': 1}


@render_to('add-location.html')
@login_required
def add_location(request):
    message = None
    form = LocationForm(request.POST or None)
    if form.is_valid():
        Box(box_type_id=6, name=form.cleaned_data['name']).save()
        message = 'Узел добавлен'
        form = LocationForm()
    return {'form': form,
            'message': message,
            'message_status': 1}


@ajax_request
def ajax_add_location(request):
    """
    Returns:
        location: string
        id: int - Box id
    """
    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'location' in POST:
            location = POST.get('location')
            box = Box(box_type_id=6, name=location)
            box.save()
            return {'location': location,
                    'id': box.pk}


@render_to('reports/inventory.html')
@login_required
def reports_inventory(request):
    def filter_results(item, person, location):
        """
        Args:
            item: Item
            person, location: Box
        Returns:
            Queryset of InventoryItems
        """
        items = InventoryItem.objects.all()
        if item:
            items = items.filter(item=item)
        if person:
            items = items.filter(box=person)
        if location:
            items = items.filter(box=location)
        return items

    items = None
    form = InventoryReportForm(request.POST or None)
    if form.is_valid():
        items = filter_results(form.cleaned_data['item'],
                               form.cleaned_data['person'],
                               form.cleaned_data['location'])
        items = items.order_by('box__box_type', 'box__name', 'item__name')
    return {'form': form, 'items': items}


@render_to('reports/statistics.html')
@login_required
def reports_statistics(request):
    def get_items(user, period, date_from, date_to):
        def get_all_items():
            def get():
                items = []
                datetime_to = convert_date_to_datetime(date_to)
                requests = Request.objects.filter(request_type__pk=2,
                                                  processed=1,
                                                  date__range=(date_from, datetime_to))
                if user is not None:
                    requests = requests.filter(user=user)
                for request in requests:
                    packet_items = PacketItem.objects.filter(packet=request.packet).exclude(box_id=1)
                    for packet_item in packet_items:
                        items.append((packet_item.item, packet_item.quantity))
                return items

            def summ_duplicates():
                output = {}
                for item in items:
                    name = item[0]
                    qty = item[1]
                    if name in output:
                        output[name] += qty
                    else:
                        output[name] = qty
                return output

            items = get()
            return summ_duplicates()

        def get_stats():
            def get_period_qty():
                qty = total_qty / float(delta) * period
                return round(qty, 2)

            def sort(output):
                collator = PyICU.Collator.createInstance(PyICU.Locale('ru_RU.UTF-8'))
                output = sorted(output, key=itemgetter(0), cmp=collator.compare)
                return output

            delta = (date_to - date_from).days
            output = []
            for item in items:
                total_qty = items[item]
                data = (item.name, total_qty, get_period_qty())
                output.append(data)
            return sort(output)

        items = get_all_items()
        items = get_stats()
        return items

    form = StatsReportForm(request.POST or None)
    items = None
    if form.is_valid():
        user = form.cleaned_data['user']
        period = form.cleaned_data['period']
        date_from = form.cleaned_data['date_from']
        date_to = form.cleaned_data['date_to']

        items = get_items(user, period, date_from, date_to)
    # returns dates_initial because it's more convinient for js form reset
    return {'form': form, 'items': items, 'dates_initial': get_dates_initial(load_dates_initial_stats())}


@render_to('reports/inventory-storage.html')
@login_required
def reports_inventory_storage(request):
    """
    Gets items with quantity lower or equal to minimal
    Returns: list of tuples:
        (string, int, int) - (item name, item quantity, item minimal quantity)
    """
    items = Item.objects.filter(deleted=False).order_by('name')
    items = [(item.name, get_quantity_in_inventory(1, item), item.minimal_quantity_in_storage)
             for item in items
             if not is_enough_item_in_inventory(1, item, item.minimal_quantity_in_storage)
             ]
    return {'items': items}


def get_dates_initial(dates):
    """
    Returns formatted list of initial dates
    Returns: list of datetime objects
    """
    return [date.strftime(settings.FORMAT_DATE) for date in dates]


@render_to('reports/movements.html')
@login_required
def reports_movements(request):
    def filter_results(item, box, box_from, box_to, date_from, date_to):
        """
        Args:
            item: Item
            box, box_from, box_to: Box
            date_from, date_to: datetime objects
        Returns:
            Queryset of Movements
        """
        movements = Movement.objects.all()
        if item:
            movements = movements.filter(item=item)
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
    # returns dates_initial variable because it's more convinient for js form reset
    return {'form': form,
            'movements': movements,
            'dates_initial': get_dates_initial(load_dates_initial())}


class RequestData:
    'Attr: request_type: int - request type pk'
    def __init__(self, request_type):
        self.request_type = request_type

    def get_item_names_in_boxes_json(self):
        """
        Returns string json - list of tuples:
            (int, (int, string)) - (Box pk, (Item pk, Item name))
        """
        if self.request_type == 1:  # in
            boxes = (Box.objects.filter(box_type=1) |  # storage
                     Box.objects.filter(box_type=6))  # locations
        else:
            boxes = Box.objects.filter(box_type=5)  # persons
        item_names_in_boxes = []
        for box in boxes:
            inventory_items = InventoryItem.objects.filter(box=box).order_by('item__name')
            item_names_in_box = [(item.item.pk, item.item.name) for item in inventory_items]
            item_names_in_boxes.append((box.pk, item_names_in_box))
        return json.dumps(item_names_in_boxes)

    def get_choices_json(self):
        'Returns json of Choices'
        if self.request_type == 1:  # in
            choices = Choices().storage_with_locations
        else:
            choices = Choices().expense_and_storage_with_locations
        return json.dumps(choices)


@render_to('requests/add.html')
def requests_add(request, request_type):
    'Attrs: request_type: int - RequestType pk'
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


def clean_json(data):
    data = data.replace('\t', ' ')
    return json.loads(data)


@ajax_request
def ajax_check_availability_receipt(request):
    def sum_duplicates(items):
        output = {}
        for item in items:
            box_and_item = (int(item[0]), int(item[1]))
            quantity = int(item[2])
            if box_and_item in output:
                output[box_and_item] += quantity
            else:
                output[box_and_item] = quantity
        return output

    def is_enough_items_in_inventory(items_request, is_process_form):
        def get_items_already_requested():
            output = []
            requests = Request.objects.filter(processed=False)
            for request in requests:
                packet = request.packet
                items = PacketItem.objects.filter(packet=packet)
                for item in items:
                    output.append((item.box_id, item.item_id, item.quantity))
            return sum_duplicates(output)
        message = None
        status = True
        items_already_requested = {}
        if not is_process_form:
            items_already_requested = get_items_already_requested()
        for item_request in items_request:
            box_id = item_request[0]
            item_id = item_request[1]
            box = Box.objects.get(pk=box_id)
            item = Item.objects.get(pk=item_id)
            quantity = items_request[item_request]
            item_already_requested = items_already_requested.get((box_id, item_id))
            if item_already_requested:
                already_requested_text = u'уже выписано %d, ' % item_already_requested
            else:
                item_already_requested = 0
                already_requested_text = ''
            if not is_enough_item_in_inventory(box, item, quantity + item_already_requested):
                message = (u'Недостаточно "%s" в "%s" (необходимо %d, %sв наличие %d)' %
                           (item.name,
                            box.name,
                            quantity,
                            already_requested_text,
                            get_quantity_in_inventory(box, item)))
                status = False
                break
        return (status, message)

    if request.is_ajax() and request.method == 'POST':
        POST = request.POST
        if 'item_data' in POST:
            items = sum_duplicates(clean_json(POST.get('item_data')))
            is_process_form = json.loads(POST.get('is_process_form'))
            status, message = is_enough_items_in_inventory(items, is_process_form)
            return {'status': status, 'message': message}


@ajax_request
def ajax_check_availability_expense(request):
    def sum_duplicates(items_request):
        output = {}
        for item_request in items_request:
            item_id = item_request[1]
            quantity = int(item_request[2])
            if item_id in output:
                output[item_id] += quantity
            else:
                output[item_id] = quantity
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
            items_request = clean_json(POST.get('item_data'))
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


@render_to('requests/list-mine.html')
@login_required
def requests_list_mine(request):
    return {'requests': Request.objects.filter(processed=0, user=request.user)}


def get_packet_items_json(packet):
    packet_items = PacketItem.objects.filter(packet=packet)
    output = []
    for item in packet_items:
        output.append((item.box.pk, item.item.pk, item.quantity, item.comment))
    return json.dumps(output)


@render_to('requests/view.html')
@login_required
def requests_view(request, id):
    request_item = Request.objects.get(pk=id)
    request_type = request_item.request_type
    person = request_item.person
    packet = request_item.packet
    request_data = RequestData(request_type.pk)
    return {'boxes': request_data.get_choices_json(),
            'item_names_in_boxes': request_data.get_item_names_in_boxes_json(),
            'request_type': request_type,
            'person': person,
            'date': request_item.date,
            'packet_id': packet.pk,
            'packet_items': get_packet_items_json(packet)}


@render_to('requests/process.html')
@permission_required(generic_permission)
@login_required
def requests_process(request, id):
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
                """
                    Not required to check if the move has been successful
                    because it is supposed to be always successful since only
                    one administrator is going to work with this. If multiple
                    admins suddenly emerge this issue will have to be addressed.
                """
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
            'date': request_item.date,
            'request_user': request_item.user,
            'packet_id': packet.pk,
            'packet_items': get_packet_items_json(packet)}


@render_to('stocktaking/list.html')
@login_required
@permission_required(generic_permission)
def stocktaking_list(request):
    # exclude receipt, expense and stocktaking boxes and also deleted ones
    boxes = Box.objects.exclude(deleted=True, box_type__in=[2, 3, 4])
    boxes = boxes.order_by('box_type', 'name')
    return {'boxes': boxes}


@render_to('stocktaking/process.html')
@permission_required(generic_permission)
@login_required
def stocktaking_process(request, box_id):
    def get_all_item_names_from_box():
        return InventoryItem.objects.filter(box=box_id).order_by('item__name')

    def get_items_in_box():
        items = get_all_item_names_from_box()
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
                items = get_all_item_names_from_box()
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
                if difference[1]:  # action
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


@render_to('requests/list-processed.html')
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
    # returns dates_initial because it's more convinient for js form reset
    return {'form': form, 'items': items, 'dates_initial': get_dates_initial(load_dates_initial())}
