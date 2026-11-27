from django.contrib.auth.models import Permission
from django.db.models import Q

from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend
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


class FilterBackend(DjangoFilterBackend):
    """
    Filters by the view's filterset_class. A wrong value fails the request as other parameters of the API do,
    and the filter set stays on the view as `filterset`, for the response to tell about the filters.
    """
    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset
        if not filterset.is_valid():
            raise serializers.ValidationError({name: [BAD_PARAMETER] for name in filterset.errors})
        view.filterset = filterset
        return filterset.qs


def ensure_session(request):
    if hasattr(request, 'session') and not request.session.session_key:
        request.session.save()
        request.session.modified = True


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


# Permissions to read every account or every order through the API, see reads_all()
READ_USERS = 'shop.api_read_users'
READ_ORDERS = 'shop.api_read_orders'


def reads_all(request, perm):
    """
    Whether the caller may read every record of a kind: perm (READ_USERS or READ_ORDERS), given to the account or one
    of its groups. Unlike has_perm(), it is not implied by is_superuser, so that an admin's token doesn't open the
    customers to whoever gets hold of it.
    """
    user = request.user
    if not (user and user.is_authenticated and user.is_active):
        return False
    if not hasattr(user, '_reads_all'):  # asked several times a request, by the permission, queryset and serializer
        user._reads_all = {
            f'{app_label}.{codename}' for app_label, codename in Permission.objects.filter(
                Q(user=user) | Q(group__user=user), codename__in=('api_read_users', 'api_read_orders'),
            ).values_list('content_type__app_label', 'codename')
        }
    return perm in user._reads_all


class ReadsAllUsers(BasePermission):
    """ Reading only, by the holder of READ_USERS, see reads_all() """
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS and reads_all(request, READ_USERS)


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
