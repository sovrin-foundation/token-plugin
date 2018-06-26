from plenum.common.messages.fields import MapField, \
    NonNegativeNumberField, NonEmptyStringField, FixedLengthField, IterableField, SignatureField
from plenum.config import SIGNATURE_FIELD_LIMIT
from sovtoken.messages.fields import PublicInputsField, \
    PublicOutputsField


class FeesStructureField(MapField):
    def __init__(self, **kwargs):
        super().__init__(NonEmptyStringField(), NonNegativeNumberField(),
                         **kwargs)


class TxnFeesField(FixedLengthField):
    _base_types = (list, tuple)
    inputs_validator = PublicInputsField()
    outputs_validator = PublicOutputsField()
    signatures_validator = IterableField(SignatureField(max_length=SIGNATURE_FIELD_LIMIT))

    def __init__(self, **kwargs):
        super().__init__(length=3, **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        error = self.inputs_validator.validate(val[0])
        if error:
            return error

        error = self.outputs_validator.validate(val[1])
        if error:
            return error

        error = self.signatures_validator.validate(val[2])
        if error:
            return error
