import json
import plenum.test.helper as plenum_helper

from sovtoken.constants import RESULT


class HelperSdk():
    """
    HelperSdk is a class which abstracts away the looper, pool_handle, and
    node_pool in the sdk calls.

    # Methods

    - get_first_result

    ## methods for sending request objects
    - prepare_request_objects
    - send_and_check_request_objects
    - send_request_objects

    ## ported sdk methods
    - sdk_get_and_check_replies
    - sdk_send_and_check
    - sdk_send_signed_requests
    """

    def __init__(self, looper, pool_handle, node_pool):
        self._looper = looper
        self._pool_handle = pool_handle
        self._node_pool = node_pool

    def get_first_result(self, request_response_list):
        """ Gets the result field from the first response. """
        return request_response_list[0][1][RESULT]

    # =============
    # Request object methods
    # =============
    # Methods for sending Request from plenum.common.request

    def prepare_request_objects(self, request_objects):
        """ Prepares the request to be sent by transforming it into json. """
        return [json.dumps(request.as_dict) for request in request_objects]

    def send_and_check_request_objects(self, request_objects):
        """
        Sends the request objects and checks the replies are valid.

        Returns a list of request_response tuples.
        """
        requests = self.prepare_request_objects(request_objects)
        return self.sdk_send_and_check(requests)

    def send_request_objects(self, request_objects):
        """ Sends the request objects """
        requests = self.prepare_request_objects(request_objects)
        return self.sdk_send_signed_requests(requests)

    # =============
    # Methods ported from plenum helper
    # =============

    def sdk_get_and_check_replies(self, req_resp_sequence, timeout=None):
        return plenum_helper.sdk_get_and_check_replies(
            self._looper,
            req_resp_sequence,
            timeout
        )

    def sdk_send_signed_requests(self, requests_signed):
        return plenum_helper.sdk_send_signed_requests(
            self._pool_handle,
            requests_signed,
        )

    def sdk_send_and_check(self, requests_signed, timeout=None):
        return plenum_helper.sdk_send_and_check(
            requests_signed,
            self._looper,
            self._node_pool,
            self._pool_handle,
            timeout
        )
