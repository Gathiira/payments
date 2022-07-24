from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from payments.models import Transaction, PaymentMethod


@registry.register_document
class PaymentMethodDocument(Document):

    class Index:
        # Name of the Elasticsearch index (must be in small letters)
        name = 'paymentmethods'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = PaymentMethod  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'name',
            'code',
            'type',
            'islog',
            'is_active',
            'date_created'
        ]


@registry.register_document
class TransactionDocument(Document):
    method = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'code': fields.TextField(),
        'type': fields.TextField()
    })
    type = fields.TextField(attr='provider_to_string')

    class Index:
        # Name of the Elasticsearch index (must be in small letters)
        name = 'transactions'
        # See Elasticsearch Indices API reference for available settings
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Transaction  # The model associated with this Document

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'id',
            'provider',
            'account_number',
            'phone_number',
            'transaction_ref',
            'currency',
            'country',
            'city',
            'narration',
            'status',
            'amount',
            'error_message',
            'instruction_to_customer',
            'transaction_is_log',
            'provider_reference',
            'amount_paid',
            'last_payment',
            'first_name',
            'last_name',
            'email',
            'payment_category',
            'date_created'
        ]

        # Ignore auto updating of Elasticsearch when a model is saved
        # or deleted:
        # ignore_signals = True

        # Don't perform an index refresh after every update (overrides global setting):
        # auto_refresh = False

        # Paginate the django queryset used to populate the index with the specified size
        # (by default it uses the database driver's default setting)
        # queryset_pagination = 5000
