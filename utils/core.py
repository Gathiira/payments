import phonenumbers


def validate_phone_number(phonenumber):
    """
    validating phone number with international formats
    Args:
        phonenumber:

    Returns:
    - a formatted kenyan phone number with +254
    """
    try:
        _number = phonenumbers.parse(phonenumber, region="KE")
        e164_format = phonenumbers.format_number(
            _number, phonenumbers.PhoneNumberFormat.E164
        )
    except phonenumbers.NumberParseException:
        return False
    is_valid = phonenumbers.is_valid_number_for_region(_number, "KE")
    if not is_valid:
        return False

    return e164_format
