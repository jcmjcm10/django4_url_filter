# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import operator

from django import forms
from django.http import Http404
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.backends.plain import PlainFilterBackend
from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.constants import StrictMode
from url_filter.filters import CallableFilter, Filter, form_field_for_filter
from url_filter.filtersets import ModelFilterSet
from url_filter.filtersets.plain import PlainModelFilterSet
from url_filter.filtersets.sqlalchemy import SQLAlchemyModelFilterSet

from . import alchemy
from .models import Place, Restaurant, Waiter


class PlaceSerializer(ModelSerializer):
    class Meta(object):
        model = Place
        exclude = []


class RestaurantSerializer(ModelSerializer):
    place = PlaceSerializer()

    class Meta(object):
        model = Restaurant
        exclude = []


class WaiterNestedSerializer(ModelSerializer):
    restaurant = RestaurantSerializer()

    class Meta(object):
        model = Waiter
        exclude = []


class WaiterSerializer(ModelSerializer):
    class Meta(object):
        model = Waiter
        exclude = []


class RestaurantNestedSerializer(ModelSerializer):
    place = PlaceSerializer()
    waiters = WaiterSerializer(source="waiter_set", many=True)

    class Meta(object):
        model = Restaurant
        exclude = []


class RestaurantNestedWithoutPlaceSerializer(ModelSerializer):
    waiters = WaiterSerializer(source="waiter_set", many=True)

    class Meta(object):
        model = Restaurant
        exclude = []


class PlaceNestedSerializer(ModelSerializer):
    restaurant = RestaurantNestedWithoutPlaceSerializer()

    class Meta(object):
        model = Place
        exclude = []


class PlaceWaiterCallableFilter(CallableFilter):
    @form_field_for_filter(forms.CharField())
    def filter_exact_for_django(self, queryset, spec):
        f = queryset.filter if not spec.is_negated else queryset.exclude
        return f(restaurant__waiter__name=spec.value)

    @form_field_for_filter(forms.CharField())
    def filter_exact_for_sqlalchemy(self, queryset, spec):
        op = operator.eq if not spec.is_negated else operator.ne
        return (
            queryset.join(alchemy.Place.restaurant)
            .join(alchemy.Restaurant.waiter_set)
            .filter(op(alchemy.Waiter.name, spec.value))
        )

    @form_field_for_filter(forms.CharField())
    def filter_exact_for_plain(self, queryset, spec):
        def identity(x):
            return x

        def negate(x):
            return not x

        op = identity if not spec.is_negated else negate
        return filter(
            lambda i: op(
                self.root.filter_backend._filter_by_spec_and_value(
                    item=i, components=["restaurant", "waiters", "name"], spec=spec
                )
            ),
            queryset,
        )


class PlaceFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail
    waiter = PlaceWaiterCallableFilter(no_lookup=True)

    class Meta(object):
        model = Place


class PlainPlaceFilterSet(PlainModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = PlainFilterBackend
    waiter = PlaceWaiterCallableFilter(no_lookup=True)

    class Meta(object):
        model = {
            "id": 1,
            "restaurant": {
                "place": 1,
                "waiters": [
                    {"id": 1, "name": "Joe", "restaurant": 1},
                    {"id": 2, "name": "Jonny", "restaurant": 1},
                ],
                "serves_hot_dogs": True,
                "serves_pizza": False,
            },
            "name": "Demon Dogs",
            "address": "944 W. Fullerton",
        }


class SQLAlchemyPlaceFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend
    waiter = PlaceWaiterCallableFilter(no_lookup=True)

    class Meta(object):
        model = alchemy.Place


class RestaurantFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail
    place_id = Filter(forms.IntegerField(min_value=0))

    class Meta(object):
        model = Restaurant


class SQLAlchemyRestaurantFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Restaurant


class WaiterFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Waiter


class SQLAlchemyWaiterFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail

    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Waiter


class PlaceViewSet(ReadOnlyModelViewSet):
    queryset = Place.objects.all()
    serializer_class = PlaceNestedSerializer
    filter_class = PlaceFilterSet


class PlainPlaceViewSet(ReadOnlyModelViewSet):
    serializer_class = PlaceNestedSerializer
    queryset = Place.objects.all()
    filter_class = PlainPlaceFilterSet

    def get_queryset(self):
        qs = super(PlainPlaceViewSet, self).get_queryset()
        data = self.get_serializer(instance=qs.all(), many=True).data
        return data

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return Response(queryset)

    def retrieve(self, request, pk):
        instance = next(
            iter(filter(lambda i: i.get("id") == int(pk), self.get_queryset())), None
        )
        if not instance:
            raise Http404
        return Response(instance)


class SQLAlchemyPlaceViewSet(ReadOnlyModelViewSet):
    serializer_class = PlaceNestedSerializer
    filter_class = SQLAlchemyPlaceFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Place)


class RestaurantViewSet(ReadOnlyModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantNestedSerializer
    filter_class = RestaurantFilterSet


class SQLAlchemyRestaurantViewSet(ReadOnlyModelViewSet):
    serializer_class = RestaurantNestedSerializer
    filter_class = SQLAlchemyRestaurantFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Restaurant)


class WaiterViewSet(ReadOnlyModelViewSet):
    queryset = Waiter.objects.all()
    serializer_class = WaiterNestedSerializer
    filter_class = WaiterFilterSet


class SQLAlchemyWaiterViewSet(ReadOnlyModelViewSet):
    serializer_class = WaiterNestedSerializer
    filter_class = SQLAlchemyWaiterFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Waiter)
