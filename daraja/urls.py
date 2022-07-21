from django.urls import path

from daraja import views as daraja_views

urlpatterns = [
    path(
        'initiate-stkpush',
        daraja_views.MpesaRegisterUrlView.as_view(),
        name='daraja-initiate-stkpush'
    ),
    path(
        "stkpush/<int:account_number>/callback",
        daraja_views.MpesaStkPushCallbackView.as_view(),
        name="transaction-stkpush-callback",
    ),
    path(
        'c2b-register-urls',
        daraja_views.MpesaRegisterUrlView.as_view(),
        name='c2b-register-urls'
    ),
    path(
        'c2b-validation-url',
        daraja_views.MpesaValidationUrlView.as_view(),
        name='c2b-validation-url'
    ),
    path(
        'c2b-confirmation-url',
        daraja_views.MpesaConfirmationUrlView.as_view(),
        name='c2b-confirmation-url'
    )
]
