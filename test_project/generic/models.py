# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

import six
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


@six.python_2_unicode_compatible
class ModelA(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


@six.python_2_unicode_compatible
class ModelB(models.Model):
    name = models.CharField(max_length=64)
    a = models.ForeignKey(
        ModelA, blank=True, null=True, related_name="rel_b", on_delete=models.CASCADE
    )
    content_type = models.ForeignKey(
        ContentType, related_name="+", on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.name
