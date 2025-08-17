from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

PAGE_SIZE = 6


class PageNumberPaginationConfig(PageNumberPagination):
    page_size = PAGE_SIZE
    page_size_query_param = 'limit'


def add_object(model, serializer_instance, serializer_class,
               already_added_message, context=None, **filter_kwargs):
    obj, created = model.objects.get_or_create(**filter_kwargs)
    if not created:
        return Response({'detail': already_added_message},
                        status=status.HTTP_400_BAD_REQUEST)
    serializer = serializer_class(serializer_instance, context=context)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def remove_object(model, not_found_message, **filter_kwargs):
    deleted, _ = model.objects.filter(**filter_kwargs).delete()
    if not deleted:
        return Response({'detail': not_found_message},
                        status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_204_NO_CONTENT)
