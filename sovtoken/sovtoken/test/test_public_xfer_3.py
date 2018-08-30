from plenum.common.txn_util import get_seq_no
from sovtoken.constants import OUTPUTS
from sovtoken.util import update_token_wallet_with_result
from sovtoken.test.helper import send_xfer, send_get_utxo
from sovtoken.test.helper import \
    user1_address, user1_token_wallet, user2_address, user2_token_wallet, \
    user3_address, user3_token_wallet


def test_same_input_address_multiple_seq_nos(tokens_distributed, looper,  # noqa
                                             sdk_pool_handle, sdk_wallet_client,
                                             seller_token_wallet, seller_address,
                                             user1_address, user2_address,
                                             user3_address, user1_token_wallet,
                                             user2_token_wallet):
    # Send a PUBLIC_XFER with inputs using the same address but different
    # sequence nos.
    global seller_gets
    seq_no_1 = tokens_distributed

    for (w, a) in [(user1_token_wallet, user1_address),
                   (user2_token_wallet, user2_address)]:
        inputs = [[w, a, seq_no_1],]
        amount = w.get_total_address_amount(address=a)
        outputs = [{"address": seller_address, "amount": amount}]
        send_xfer(looper, inputs, outputs, sdk_pool_handle)

    res1 = send_get_utxo(looper, seller_address, sdk_wallet_client,
                         sdk_pool_handle)
    assert len(res1[OUTPUTS]) > 1

    update_token_wallet_with_result(seller_token_wallet, res1)
    inputs = []
    output_amount = 0
    for s, amt in list(seller_token_wallet.get_all_address_utxos(seller_address).values())[0]:
        inputs.append([seller_token_wallet, seller_address, s])
        output_amount += amt

    outputs = [{"address": user3_address, "amount": output_amount}]
    new_seq_no = get_seq_no(send_xfer(looper, inputs, outputs, sdk_pool_handle))

    res2 = send_get_utxo(looper, user3_address, sdk_wallet_client,
                         sdk_pool_handle)

    assert len(res2[OUTPUTS]) > 0
    for output in res2[OUTPUTS]:
        if output["seqNo"] == new_seq_no:
            assert output["amount"] == output_amount
            break
    else:
        raise AssertionError('Needed to find output {}:{} with val {} but not '
                             'found'.format(user3_address, new_seq_no,
                                            output_amount))
