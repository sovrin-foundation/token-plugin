from plenum.common.messages.fields import FieldBase, Base58Field, MapField, \
    NonNegativeNumberField, NonEmptyStringField, FixedLengthField
from plenum.server.plugin.token.src.messages.fields import PublicInputsField, \
    PublicOutputsField


class FeesStructureField(MapField):
    def __init__(self, **kwargs):
        super().__init__(NonEmptyStringField(), NonNegativeNumberField(),
                         **kwargs)


class TxnFeesField(FixedLengthField):
    _base_types = (list, tuple)
    inputs_validator = PublicInputsField()
    outputs_validator = PublicOutputsField()

    def __init__(self, **kwargs):
        super().__init__(length=2, **kwargs)

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
