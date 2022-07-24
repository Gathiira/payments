
from django.urls import path

from search.views import (
    SearchPaymentMethodView,
    SearchTransactionView,
    PaymentMethodDetailView,
    TransactionDetailView
)
urlpatterns = [
    path(
        'payment-methods/',
        SearchPaymentMethodView.as_view(),
        name='search-payment-methods'
    ),
    path(
        'payment-method/<str:query>/',
        PaymentMethodDetailView.as_view(),
        name='search-payment-methods'
    ),
    path(
        'transactions/',
        SearchTransactionView.as_view(),
        name='search-transactions'
    ),
    path(
        'transaction/<str:query>/',
        TransactionDetailView.as_view(),
        name='search-transactions'
    ),
]
