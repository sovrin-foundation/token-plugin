from plenum.common.messages.fields import MapField, \
    NonNegativeNumberField, NonEmptyStringField, FixedLengthField, IterableField, SignatureField
from plenum.config import SIGNATURE_FIELD_LIMIT

from sovtoken.messages.fields import PublicInputsField, \
    PublicOutputsField
from sovtokenfees.constants import MAX_FEE_OUTPUTS
from sovtoken.transactions import TokenTransactions

ALLOWED_FEES_TXNS = [
    TokenTransactions.XFER_PUBLIC.value,
    "1", #NYM
    "100", #ATTRIB
    "101", #SCHEMA
    "102", #CRED_DEF
    "113", #REVOC_REG_DEF
    "114", #REVOC_REG_ENTRY
]

# WARNING: This validation is a temporary solution!
# Set of allowed transactions should be moved to config ledger.

class FeesStructureField(MapField):
    def __init__(self, **kwargs):
        super().__init__(NonEmptyStringField(), NonNegativeNumberField(),
                         **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return "set_fees -- " + error

        for (k, _) in val.items():
            if not k in ALLOWED_FEES_TXNS:
                return "set_fees -- Fees are not allowed for txn " + k


class TxnFeesField(FixedLengthField):
    _base_types = (list, tuple)
    inputs_validator = PublicInputsField(min_length=1)
    outputs_validator = PublicOutputsField(max_length=MAX_FEE_OUTPUTS)
    signatures_validator = IterableField(SignatureField(max_length=SIGNATURE_FIELD_LIMIT))

    def __init__(self, **kwargs):
        super().__init__(length=3, **kwargs)

    def _specific_validation(self, val):
        error = super()._specific_validation(val)
        if error:
            return "fees -- " + error

        error = self.inputs_validator.validate(val[0])
        if error:
            return "inputs -- " + error

        error = self.outputs_validator.validate(val[1])
        if error:
            return "outputs -- " + error

        error = self.signatures_validator.validate(val[2])
        if error:
            return "signatures -- " + error

        if len(val[0]) != len(val[2]):
            return 'signatures -- Number of signatures and number of inputs should match but are {} and {} ' \
                   'respectively.'.format(len(val[2]), len(val[0]))