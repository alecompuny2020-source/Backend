from rest_framework.pagination import PageNumberPagination

class GenericEnteprisePaginator(PageNumberPagination):
    """A custom pagination to provide consistent paginated response"""
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
