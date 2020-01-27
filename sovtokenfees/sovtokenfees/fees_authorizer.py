from sovtoken.request_handlers.token_utils import TokenStaticHelper

from indy_common.authorize.authorizer import AbstractAuthorizer

from indy_common.authorize.auth_constraints import AuthConstraint

from indy_common.authorize.auth_actions import AbstractAuthAction
from sovtoken.constants import XFER_PUBLIC, AMOUNT, INPUTS, OUTPUTS
from sovtoken.exceptions import UTXOError, InvalidFundsError, ExtraFundsError, InsufficientFundsError
from sovtoken.utxo_cache import UTXOCache
from sovtokenfees.constants import FEES_FIELD_NAME, FEES
from sovtokenfees.domain import build_path_for_set_fees
from stp_core.common.log import getlogger

from plenum.common.exceptions import UnauthorizedClientRequest, InvalidClientMessageException

from state.pruning_state import PruningState

from plenum.common.constants import TXN_TYPE

from common.serializers.json_serializer import JsonSerializer

logger = getlogger()


class FeesAuthorizer(AbstractAuthorizer):
    def __init__(self,
                 config_state: PruningState,
                 utxo_cache: UTXOCache):
        super().__init__()
        self.config_state = config_state
        self.utxo_cache = utxo_cache
        self.state_serializer = JsonSerializer()

    @staticmethod
    def has_fees(request) -> bool:
        return hasattr(request, FEES) and request.fees is not None

    @staticmethod
    def get_change_for_fees(request) -> list:
        return request.fees[1] if len(request.fees) >= 2 else []

    @staticmethod
    def calculate_fees_from_req(utxo_cache, request):
        if hasattr(request, FEES):
            inputs = request.fees[0]
            outputs = FeesAuthorizer.get_change_for_fees(request)
        else:
            inputs = request.operation[INPUTS]
            outputs = request.operation[OUTPUTS]
        try:
            sum_inputs = utxo_cache.sum_inputs(inputs, is_committed=False)
        except Exception as e:
            logger.error("Unexpected exception while sum_inputs calculating: {}".format(e))
            return 0

        sum_outputs = sum([a[AMOUNT] for a in outputs])
        return sum_inputs - sum_outputs

    def can_pay_fees(self, request, required_fees):
        try:
            self._can_pay_fees(request, required_fees)
        except (InvalidFundsError, UnauthorizedClientRequest, ExtraFundsError,
                InsufficientFundsError, InvalidClientMessageException) as e:
            return False, str(e)

        return True, ''

    def _can_pay_fees(self, request, required_fees):

        if request.operation[TXN_TYPE] == XFER_PUBLIC:
            # Fees in XFER_PUBLIC is part of operation[INPUTS]
            inputs = request.operation[INPUTS]
            outputs = request.operation[OUTPUTS]
            self._validate_fees_can_pay(request, inputs, outputs, required_fees)
        else:
            inputs = request.fees[0]
            outputs = self.get_change_for_fees(request)
            self._validate_fees_can_pay(request, inputs, outputs, required_fees)

    def _validate_fees_can_pay(self, request, inputs, outputs, required_fees):
        """
        Calculate and verify that inputs and outputs for fees can both be paid and change is properly specified

        This function ASSUMES that validation of the fees for the request has already been done.

        :param request:
        :param required_fees:
        :return:
        """

        try:
            sum_inputs = self.utxo_cache.sum_inputs(inputs, is_committed=False)
        except UTXOError as ex:
            raise InvalidFundsError(request.identifier, request.reqId, "{}".format(ex))
        except Exception as ex:
            error = 'Exception {} while processing inputs/outputs'.format(ex)
            raise UnauthorizedClientRequest(request.identifier, request.reqId, error)
        else:
            change_amount = sum([a[AMOUNT] for a in outputs])
            expected_amount = change_amount + required_fees
            TokenStaticHelper.validate_given_inputs_outputs(
                sum_inputs,
                change_amount,
                expected_amount,
                request,
                'fees: {}'.format(required_fees)
            )

    def _get_fees_alias_from_constraint(self, auth_constaint: AuthConstraint):
        if auth_constaint.metadata:
            if FEES_FIELD_NAME in auth_constaint.metadata:
                return auth_constaint.metadata[FEES_FIELD_NAME]

    def _get_fees_from_state(self):
        key = build_path_for_set_fees()
        serz = self.config_state.get(key,
                                     isCommitted=False)
        if not serz:
            return {}
        return self.state_serializer.deserialize(serz)

    def authorize(self,
                  request,
                  auth_constraint: AuthConstraint,
                  auth_action: AbstractAuthAction=None):
        fees_alias = self._get_fees_alias_from_constraint(auth_constraint)
        fees = self._get_fees_from_state()
        fees_amount = fees.get(fees_alias, 0)
        is_fees_required = fees_amount > 0
        if request.txn_type != XFER_PUBLIC:
            if is_fees_required and not self.has_fees(request):
                logger.debug("Validation error: Fees are required for this txn type")
                return False, "Fees are required for this txn type"
            if not is_fees_required and self.has_fees(request) \
                    and self.calculate_fees_from_req(self.utxo_cache, request) > 0:
                logger.debug("Validation error: Fees are not required for this txn type")
                return False, "Fees are not required for this txn type"
            if not is_fees_required and not self.has_fees(request):
                return True, ""
        return self.can_pay_fees(request, fees_amount)
