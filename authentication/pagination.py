from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AuthorsPaginator(PageNumberPagination):

    page_size = 20
    page_query_param = 'p'

    def get_paginated_response(self, data):
        return Response({
            'total': self.page.paginator.num_pages,
            'results': data
        })