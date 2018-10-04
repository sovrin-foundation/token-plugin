import pytest

from plenum.common.constants import (ROLE, TARGET_NYM, TRUSTEE, TRUSTEE_STRING,
                                     VERKEY, NYM)
from plenum.common.txn_util import get_payload_data

from sovtoken.constants import ADDRESS, AMOUNT


def get_nym_details(helpers, dest):
    domain_req_handler = helpers.node.get_domain_req_handler()
    return domain_req_handler.getNymDetails(domain_req_handler.state, dest, False)


@pytest.mark.helper_test
class TestNym:
    def test_nym_request_with_defaults(self, helpers):
        result = helpers.general.do_nym()

        data = get_payload_data(result)

        dest = data[TARGET_NYM]

        nym = get_nym_details(helpers, dest)

        assert nym != {}

    def test_nym_changes_role(self, helpers):
        result = helpers.general.do_nym(role=TRUSTEE_STRING)

        data = get_payload_data(result)

        dest = data[TARGET_NYM]
        verkey = data[VERKEY]

        nym = get_nym_details(helpers, dest)

        assert nym[ROLE] == TRUSTEE

        helpers.general.do_nym(dest=dest, verkey=verkey, role='')

        nym = get_nym_details(helpers, dest)

        assert not nym[ROLE]
