from django_slack import slack_message


def send_slack_message(transaction):
    """
    send transaction data to slack channel
    """
    slack_message(
        "transaction.slack", {"transaction": transaction}, fail_silently=False
    )
