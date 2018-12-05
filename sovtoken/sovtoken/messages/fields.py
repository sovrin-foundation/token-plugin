from base58 import b58decode_check

from plenum.common.messages.fields import FieldBase, AnyMapField, FixedLengthField, TxnSeqNoField, IterableField
from sovtoken.util import decode_address_to_vk_bytes


class PublicAddressField(FieldBase):
    _base_types = (str, )
    length = 36

    def _specific_validation(self, val):
        try:
            vk = decode_address_to_vk_bytes(val)
            if len(vk) != 32:
                return 'Not a valid address as it resolves to {} byte verkey'.format(len(vk))
        except ValueError as ex:
            return str(ex)


class PublicAmountField(FieldBase):

    _base_types = (int,)

    def _specific_validation(self, val):
        if val <= 0:
            return 'negative or zero value'


class PublicOutputField(AnyMapField):
    public_address_field = PublicAddressField()
    public_amount_field = PublicAmountField()

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        addr_error = self.public_address_field.validate(val["address"])
        if addr_error:
            return "address -- " + addr_error
        amt_error = self.public_amount_field.validate(val["amount"])
        if amt_error:
            return "amount -- " + amt_error


# class PublicAddressesField(IterableField):
#     def __init__(self, **kwargs):
#         super().__init__(inner_field_type=PublicAddressField(), **kwargs)


class PublicOutputsField(IterableField):
    def __init__(self, **kwargs):
        super().__init__(inner_field_type=PublicOutputField(), **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        if len(val) != len({a["address"] for a in val}):
            error = 'Each output should contain unique address'
        if error:
            return error


class PublicInputField(AnyMapField):
    public_address_field = PublicAddressField()
    seq_no_field = TxnSeqNoField()

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        addr_error = self.public_address_field.validate(val["address"])
        if addr_error:
            return "address -- " + addr_error
        amt_error = self.seq_no_field.validate(val["seqNo"])
        if amt_error:
            return "seqNo -- " + amt_error


class PublicInputsField(IterableField):
    def __init__(self, **kwargs):
        super().__init__(inner_field_type=PublicInputField(), **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        if len(val) != len({(a["address"], a["seqNo"]) for a in val}):
            error = 'Each input should be unique'
        if error:
            return error
