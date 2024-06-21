# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet

from url_filter.backends.sqlalchemy import SQLAlchemyFilterBackend
from url_filter.constants import StrictMode
from url_filter.filtersets import ModelFilterSet
from url_filter.filtersets.sqlalchemy import SQLAlchemyModelFilterSet

from . import alchemy
from .models import Article, Reporter


class ReporterSerializer(ModelSerializer):
    class Meta(object):
        model = Reporter
        exclude = []


class ArticleSerializer(ModelSerializer):
    class Meta(object):
        model = Article
        exclude = ["reporter"]


class ReporterNestedSerializer(ModelSerializer):
    articles = ArticleSerializer(many=True)

    class Meta(object):
        model = Reporter
        exclude = []


class ArticleNestedSerializer(ModelSerializer):
    reporter = ReporterSerializer()

    class Meta(object):
        model = Article
        exclude = []


class ReporterFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Reporter
        exclude = []


class SQLAlchemyReporterFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Reporter
        exclude = []


class ArticleFilterSet(ModelFilterSet):
    default_strict_mode = StrictMode.fail

    class Meta(object):
        model = Article
        exclude = []


class SQLAlchemyArticleFilterSet(SQLAlchemyModelFilterSet):
    default_strict_mode = StrictMode.fail
    filter_backend_class = SQLAlchemyFilterBackend

    class Meta(object):
        model = alchemy.Article
        exclude = []


class ReporterViewSet(ReadOnlyModelViewSet):
    queryset = Reporter.objects.all()
    serializer_class = ReporterNestedSerializer
    filter_class = ReporterFilterSet


class SQLAlchemyReporterViewSet(ReadOnlyModelViewSet):
    serializer_class = ReporterNestedSerializer
    filter_class = SQLAlchemyReporterFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Reporter)


class ArticleViewSet(ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleNestedSerializer
    filter_class = ArticleFilterSet


class SQLAlchemyArticleViewSet(ReadOnlyModelViewSet):
    serializer_class = ArticleNestedSerializer
    filter_class = SQLAlchemyArticleFilterSet

    def get_queryset(self):
        return self.request.alchemy_session.query(alchemy.Article)
