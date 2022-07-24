
import abc
import logging

from rest_framework.response import Response
from rest_framework import status
from elasticsearch_dsl import Q
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.views import APIView

from payments.serializers import TransactionSerializer, PaymentMethodSerializer
from payments.documents import TransactionDocument, PaymentMethodDocument

logger = logging.getLogger(__name__)


class ElasticSearchAPIView(APIView):
    serializer_class = None
    document_class = PaymentMethodDocument.search().query()

    @abc.abstractmethod
    def generate_q_expression(self, query):
        """This method should be overridden
        and return a Q() expression."""

    def get_search_queryset(self, request, query, paginate=True):
        try:
            if bool(query):
                q = self.generate_q_expression(query)
                search = self.document_class.search().query(q)
            else:
                search = self.document_class.search()
            response = search.execute()

            print(
                f'Found {response.hits.total.value} hit(s) for query: "{query}"')
            if paginate:
                results = self.paginate_queryset(response, request, view=self)
                serializer = self.serializer_class(results, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                if bool(response):
                    serializer = self.serializer_class(response, many=True)
                    return Response(serializer.data[0])
                return Response({})
        except Exception as e:
            logger.error(e)
            return Response(
                {"detail": "Failed to query Transaction. Contact Support!"},
                status=status.HTTP_400_BAD_REQUEST)


class SearchPaymentMethodView(ElasticSearchAPIView, LimitOffsetPagination):
    serializer_class = PaymentMethodSerializer
    document_class = PaymentMethodDocument

    def generate_q_expression(self, query):
        return Q(
            'multi_match', query=query,
            fields=[
                'name',
                'code'
            ], fuzziness='auto')

    def get(self, request):
        query = request.query_params.get('filter')
        return self.get_search_queryset(request, query)


class SearchTransactionView(ElasticSearchAPIView, LimitOffsetPagination):
    serializer_class = TransactionSerializer
    document_class = TransactionDocument

    def generate_q_expression(self, query):
        return Q(
            'multi_match', query=query,
            fields=[
                'account_number',
                'provider',
                'phone_number',
                'narration',
                'amount',
                'payment_category',
                'first_name',
            ])

    def get(self, request):
        query = request.query_params.get('filter')
        return self.get_search_queryset(request, query)


class PaymentMethodDetailView(ElasticSearchAPIView):
    serializer_class = PaymentMethodSerializer
    document_class = PaymentMethodDocument

    def generate_q_expression(self, query):
        return Q('bool',
                 should=[
                     Q('match', id=query),
                 ], minimum_should_match=1)

    def get(self, request, query):
        return self.get_search_queryset(request, query, paginate=False)


class TransactionDetailView(ElasticSearchAPIView):
    serializer_class = TransactionSerializer
    document_class = TransactionDocument

    def generate_q_expression(self, query):
        return Q('bool',
                 should=[
                     Q('match', id=query),
                     Q('match', account_number=query),
                 ], minimum_should_match=1)

    def get(self, request, query):
        return self.get_search_queryset(request, query, paginate=False)
