from abc import abstractmethod
from plenum.server.config_req_handler import ConfigReqHandler


class FeeReqHandler(ConfigReqHandler):
    @abstractmethod
    def can_pay_fees(self, request) -> bool:
        pass

    @abstractmethod
    def deduct_fees(self, request, *args, **kwargs) -> bool:
        pass

    def commit_fee_txns(self, txn, pp_time, state_root, txn_root):
        pass
