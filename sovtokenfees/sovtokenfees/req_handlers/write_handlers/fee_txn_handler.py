from typing import Optional

from sovtoken import TOKEN_LEDGER_ID
from sovtokenfees.constants import FEE_TXN
from sovtokenfees.req_handlers.write_handlers.xfer_fee_handler import XferFeeHandler

from indy_common.types import Request
from plenum.server.database_manager import DatabaseManager
from plenum.server.request_handlers.handler_interfaces.write_request_handler import WriteRequestHandler


class FeeTxnCatchupHandler(XferFeeHandler):

    def __init__(self, database_manager: DatabaseManager):
        super(WriteRequestHandler, self).__init__(database_manager, FEE_TXN, TOKEN_LEDGER_ID)

    def apply_request(self, request: Request, batch_ts, prev_result):
        pass

    def static_validation(self, request: Request):
        pass

    def dynamic_validation(self, request: Request, req_pp_time: Optional[int]):
        pass