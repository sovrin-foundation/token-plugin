from base58 import b58decode_check

from plenum.common.messages.fields import FieldBase, Base58Field, \
    FixedLengthField, TxnSeqNoField, IterableField
from plenum.server.plugin.token.src.util import decode_address_to_vk_bytes


class PublicAddressField(FieldBase):
    _base_types = (str, )

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


class PublicOutputField(FixedLengthField):
    _base_types = (list, tuple)
    public_address_field = PublicAddressField()
    public_amount_field = PublicAmountField()

    def __init__(self, **kwargs):
        super().__init__(length=2, **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        addr_error = self.public_address_field.validate(val[0])
        if addr_error:
            return addr_error
        amt_error = self.public_amount_field.validate(val[1])
        if amt_error:
            return amt_error


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

        if len(val) != len({a for a, _ in val}):
            error = 'Each output should contain unique address'
        if error:
            return error


class PublicInputField(FixedLengthField):
    _base_types = (list, tuple)
    public_address_field = PublicAddressField()
    seq_no_field = TxnSeqNoField()

    def __init__(self, **kwargs):
        super().__init__(length=2, **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        for (field, val) in zip((self.public_address_field, self.seq_no_field), val):
            err = field.validate(val)
            return err


class PublicInputsField(IterableField):
    def __init__(self, **kwargs):
        super().__init__(inner_field_type=PublicInputField(), **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        if len(val) != len({(a, s) for a, s in val}):
            error = 'Each input should be unique'
        if error:
            return error
