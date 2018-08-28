from plenum.common.messages.fields import MapField, AnyMapField, \
    NonNegativeNumberField, NonEmptyStringField, FixedLengthField, IterableField, SignatureField
from plenum.config import SIGNATURE_FIELD_LIMIT

from sovtoken.messages.fields import PublicInputsField, \
    PublicOutputsField
from sovtoken.constants import INPUTS, SIGS, OUTPUTS


class FeesStructureField(MapField):
    def __init__(self, **kwargs):
        super().__init__(NonEmptyStringField(), NonNegativeNumberField(),
                         **kwargs)


class TxnFeesField(AnyMapField):
    _base_types = (dict,)
    inputs_validator = PublicInputsField()
    outputs_validator = PublicOutputsField()
    signatures_validator = IterableField(SignatureField(max_length=SIGNATURE_FIELD_LIMIT))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return error

        error = self.inputs_validator.validate(val[INPUTS])
        if error:
            return error

        error = self.outputs_validator.validate(val[OUTPUTS])
        if error:
            return error

        error = self.signatures_validator.validate(val[SIGS])
        if error:
            return error

        if len(val[INPUTS]) != len(val[SIGS]):
            return 'Number of signatures and number of inputs should match but are {} and {} ' \
                   'respectively.'.format(len(val[SIGS]), len(val[INPUTS]))

