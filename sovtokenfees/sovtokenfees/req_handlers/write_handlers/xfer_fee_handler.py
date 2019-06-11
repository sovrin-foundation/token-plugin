from sovtoken.constants import XFER_PUBLIC

from indy_common.authorize.auth_actions import AuthActionAdd
from sovtoken.request_handlers.write_request_handler.xfer_handler import XferHandler

from plenum.common.request import Request


class XferFeeHandler(XferHandler):
    def dynamic_validation(self, request: Request):
        return self._write_req_validator.validate(request, [AuthActionAdd(txn_type=XFER_PUBLIC,
                                                                          field="*",
                                                                          value="*")])
