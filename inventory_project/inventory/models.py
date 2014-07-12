# -*- coding: utf8 -*-
from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    name = models.CharField('название', unique=True, max_length=255)
    minimal_quantity_in_storage = models.IntegerField(
        'минимальное необходимое количество на складе', blank=True, default=0)
    deleted = models.BooleanField('удален')

    class Meta:
        verbose_name = 'наименование'
        verbose_name_plural = 'наименования'

    def __unicode__(self):
        return self.name


class BoxType(models.Model):
    name = models.CharField('название', unique=True, max_length=255)

    class Meta:
        verbose_name = 'тип коробки'
        verbose_name_plural = 'типы коробок'

    def __unicode__(self):
        return self.name


class Network(models.Model):
    name = models.CharField('название', unique=True, max_length=255)

    class Meta:
        verbose_name = 'сеть'
        verbose_name_plural = 'сети'

    def __unicode__(self):
        return self.name


class Box(models.Model):
    name = models.CharField('название', unique=True, max_length=255)
    box_type = models.ForeignKey(BoxType, verbose_name='тип коробки')
    network = models.ForeignKey(Network, default=1, verbose_name='сеть')
    deleted = models.BooleanField('удален')

    class Meta:
        verbose_name = 'коробка'
        verbose_name_plural = 'коробки'

    def __unicode__(self):
        return self.name


class InventoryItem(models.Model):
    box = models.ForeignKey(Box, verbose_name='коробка')
    item = models.ForeignKey(Item, verbose_name='наименование')
    quantity = models.IntegerField('количество')

    class Meta:
        verbose_name = 'наличие'
        verbose_name_plural = 'наличие'

    def __unicode__(self):
        return '"%s" - "%s" (%d)' % (
            self.box.name, self.item.name, self.quantity)


class Movement(models.Model):
    box_from = models.ForeignKey(Box, related_name='box_from',
                                 verbose_name='коробка от')
    box_to = models.ForeignKey(Box, related_name='box_to',
                               verbose_name='коробка к')
    item = models.ForeignKey(Item, verbose_name='наименование')
    quantity = models.IntegerField('количество')
    date = models.DateTimeField('дата', auto_now_add=True)
    comment = models.CharField('комментарий', max_length=255, null=True,
                               blank=True)

    class Meta:
        verbose_name = 'перемещение'
        verbose_name_plural = 'перемещения'

    def __unicode__(self):
        return '"%s" -> "%s" - "%s" (%d)' % (self.box_from.name,
                                             self.box_to.name,
                                             self.item.name,
                                             self.quantity)


class Packet(models.Model):
    class Meta:
        verbose_name = 'пакет'
        verbose_name_plural = 'пакеты'


class PacketItem(models.Model):
    packet = models.ForeignKey(Packet, verbose_name='пакет')
    box = models.ForeignKey(Box, verbose_name='коробка')
    item = models.ForeignKey(Item, verbose_name='наименование')
    quantity = models.IntegerField('количество')
    comment = models.CharField('комментарий', max_length=255, null=True,
                               blank=True)

    class Meta:
        verbose_name = 'содержимое пакета'
        verbose_name_plural = 'содержимое пакета'

    def __unicode__(self):
        return '%s" (%d)' % (self.item.name, self.quantity)


class RequestType(models.Model):
    name = models.CharField('название', unique=True, max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = 'название'
        verbose_name_plural = 'названия'


class Request(models.Model):
    request_type = models.ForeignKey(RequestType, verbose_name='тип заявки')
    user = models.ForeignKey(User, verbose_name='пользователь')
    person = models.ForeignKey(Box, verbose_name='лицо')
    packet = models.ForeignKey(Packet, verbose_name='пакет', unique=True)
    date = models.DateTimeField('дата/время', auto_now_add=True)
    processed = models.BooleanField('обработано')

    class Meta:
        verbose_name = 'заявка'
        verbose_name_plural = 'заявки'

    def __unicode__(self):
        return '"%s", "%s"' % (self.user.username, self.person.name)
