from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class RepliesPaginator(PageNumberPagination):

    page_size = 6
    page_query_param = 'p'


class StoriesPaginator(PageNumberPagination):

    page_query_param = 'page'
    page_size = 9

    def get_paginated_response(self, data):
        return Response({
            'results': data,
            'total': self.page.paginator.num_pages
        })

