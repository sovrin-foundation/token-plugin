from sovtokenfees.constants import SET_FEES, FEES
from sovtokenfees.req_handlers.fees_utils import get_fee_from_state

from common.serializers.serialization import proof_nodes_serializer, state_roots_serializer, config_state_serializer
from indy_common.authorize.auth_actions import AuthActionEdit
from sovtokenfees import FeesTransactions
from sovtokenfees.messages.fields import SetFeesMsg

from plenum.common.constants import CONFIG_LEDGER_ID, BLS_LABEL, MULTI_SIGNATURE, ROOT_HASH, PROOF_NODES
from plenum.common.exceptions import InvalidClientRequest
from plenum.common.request import Request
from plenum.common.txn_util import get_payload_data
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler

from sovtokenfees.domain import build_path_for_set_fees


class SetFeesHandler(WriteRequestHandler):
    set_fees_validator_cls = SetFeesMsg

    def __init__(self, db_manager: DatabaseManager, write_req_validator):
        super().__init__(db_manager, FeesTransactions.SET_FEES.value, CONFIG_LEDGER_ID)
        self._write_req_validator = write_req_validator

    def static_validation(self, request: Request):
        try:
            self.set_fees_validator_cls(**request.operation)
        except TypeError as exc:
            raise InvalidClientRequest(request.identifier,
                                       request.reqId,
                                       exc)

    def dynamic_validation(self, request: Request):
        return self._write_req_validator.validate(request,
                                                  [AuthActionEdit(txn_type=SET_FEES,
                                                                  field="*",
                                                                  old_value="*",
                                                                  new_value="*")])

    def update_state(self, txn, prev_result, request, is_committed=False):
        payload = get_payload_data(txn)
        fees_from_req = payload.get(FEES)
        current_fees = get_fee_from_state(self.state)
        current_fees = current_fees if current_fees else {}
        current_fees.update(fees_from_req)
        for fees_alias, fees_value in fees_from_req.items():
            self._set_to_state(build_path_for_set_fees(alias=fees_alias), fees_value)
        self._set_to_state(build_path_for_set_fees(), current_fees)

    def _set_to_state(self, key, val):
        val = config_state_serializer.serialize(val)
        key = key.encode()
        self.state.set(key, val)
