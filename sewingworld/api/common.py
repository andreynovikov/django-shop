from contextlib import contextmanager

from django.db import connection

from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from drf_spectacular.utils import OpenApiResponse

from sewingworld.serializers.common import ErrorDetailSerializer

# Error responses for the API schema. NotAuthenticated is rendered as 403 too: DRF takes WWW-Authenticate
# from the first authentication class, and SessionAuthentication has none.
FORBIDDEN = OpenApiResponse(ErrorDetailSerializer, description='Not logged in or not allowed')
NOT_FOUND = OpenApiResponse(ErrorDetailSerializer, description='Not found')
THROTTLED = OpenApiResponse(ErrorDetailSerializer, description='Too many requests')

BAD_PARAMETER = 'Неверное значение'


def id_params(request, name):
    """ Values of a query parameter that takes ids: anything else would fail the query with a server error """
    values = request.query_params.getlist(name)
    if not all(value.isascii() and value.isdigit() for value in values):
        raise serializers.ValidationError({name: [BAD_PARAMETER]})
    return values


# The first key of advisory_lock(), one per kind of the object locked
ORDER_REGISTRATION_LOCK = 1


@contextmanager
def advisory_lock(kind, key):
    """
    Lets one request at a time through for the object, with a PostgreSQL session-level lock: the code inside
    commits as usual, unlike under select_for_update(). The lock is released at the end even when the code raises,
    as the connection outlives the request.
    """
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_advisory_lock(%s, %s)', [kind, key])
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_unlock(%s, %s)', [kind, key])


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'totalPages': self.page.paginator.num_pages,
            'currentPage': self.page.number,
            'pageSize': self.get_page_size(self.request),
            'results': data
        })
