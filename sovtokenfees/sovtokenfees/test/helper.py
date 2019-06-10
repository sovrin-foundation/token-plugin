import pytest
import json
from enum import Enum, unique

from sovtoken.test.helpers.helper_general import utxo_from_addr_and_seq_no
from sovtokenfees.test.constants import NYM_FEES_ALIAS, txn_type_to_alias, XFER_PUBLIC_FEES_ALIAS
from stp_core.loop.eventually import eventually

from plenum.common.constants import DOMAIN_LEDGER_ID, DATA, TXN_TYPE, NYM
from plenum.common.util import randomString
from plenum.common.types import f
from plenum.test.node_catchup.helper import waitNodeDataEquality
from plenum.test.pool_transactions.helper import prepare_nym_request, sdk_sign_and_send_prepared_request
from plenum.test.helper import sdk_json_to_request_object, sdk_sign_request_objects, sdk_send_signed_requests, \
    sdk_get_and_check_replies, assertExp

from sovtoken import TOKEN_LEDGER_ID
from sovtoken.utxo_cache import UTXOAmounts
from sovtoken.constants import OUTPUTS, AMOUNT, ADDRESS, XFER_PUBLIC, SEQNO

from sovtokenfees.constants import FEES


@unique
class InputsStrategy(Enum):
    all_utxos = 1           # use all utxos from each input address
    first_utxo_only = 2     # use only single (first) from each input address
                            # (TODO just to have some other one for now)


@unique
class OutputsStrategy(Enum):
    transfer_some_equal = 1
                # divide transfer among output addresses in (almost)
                # equal parts, a change (total_input - transfer - fee)
                # goes either to one address listed in both inputs and
                # outputs if there is such one or to the first input
                # address otherwise
    transfer_all_equal = 2
                # divide (total_input - fee) among all
                # output addresses in (almost) equal parts
                # ( useful when we move all amount to other addresses )


def check_state(n, is_equal=False):
    assert (n.getLedger(DOMAIN_LEDGER_ID).tree.root_hash == n.getLedger(DOMAIN_LEDGER_ID).uncommitted_root_hash) == is_equal
    assert (n.getLedger(TOKEN_LEDGER_ID).tree.root_hash == n.getLedger(TOKEN_LEDGER_ID).uncommitted_root_hash) == is_equal

    assert (n.getState(DOMAIN_LEDGER_ID).headHash ==
            n.getState(DOMAIN_LEDGER_ID).committedHeadHash) == is_equal

    assert (n.getState(TOKEN_LEDGER_ID).headHash ==
            n.getState(TOKEN_LEDGER_ID).committedHeadHash) == is_equal


def get_amount_from_token_txn(token_txn):
    return token_txn[f.TXN.nm][DATA][OUTPUTS][0][AMOUNT]


def check_uncommitted_txn(node, expected_length, ledger_id):
    assert len(node.getLedger(ledger_id).uncommittedTxns) == expected_length


def add_fees_request_with_address_inner(helpers, fees_set, request, address, utxos=None, change_address=None, adjust_fees=0):
    utxos = utxos if utxos else helpers.inner.general.get_utxo_addresses([address])[0]
    txn_type = request.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]]
    helpers.inner.request.add_fees(
        request,
        utxos,
        fee_amount - adjust_fees,
        change_address=change_address if change_address else address,
    )
    return request


def add_fees_request_with_address(helpers, fees_set, request, address, utxos=None, change_address=None, adjust_fees=0):
    utxos_found = utxos if utxos else helpers.general.get_utxo_addresses([address])[0]
    txn_type = request.operation[TXN_TYPE]
    fee_amount = fees_set[FEES][txn_type_to_alias[txn_type]]
    request_with_fees = helpers.request.add_fees(
        request,
        utxos_found,
        fee_amount - adjust_fees,
        change_address=change_address if change_address else address
    )[0]
    request_with_fees = json.loads(request_with_fees)
    setattr(request, FEES, request_with_fees[FEES])
    return request


def pay_fees(helpers, fees_set, address_main):
    request = helpers.request.nym()

    request = add_fees_request_with_address(
        helpers,
        fees_set,
        request,
        address_main
    )

    responses = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(responses)
    return result


def pay_fees_inner(helpers, fees_set, address_main):
    request = helpers.request.nym()

    request = add_fees_request_with_address_inner(
        helpers,
        fees_set,
        request,
        address_main
    )

    responses = helpers.sdk.send_and_check_request_objects([request])
    result = helpers.sdk.get_first_result(responses)
    return result


def get_committed_txns_count_for_pool(node_set, ledger_id):
    txns_counts = set([n.getLedger(ledger_id).size for n in node_set])
    assert len(txns_counts) == 1
    return txns_counts.pop()


def get_uncommitted_txns_count_for_pool(node_set, ledger_id):
    txns_counts = set([n.getLedger(ledger_id).uncommitted_size for n in node_set])
    assert len(txns_counts) == 1
    return txns_counts.pop()


def get_head_hash_for_pool(node_set, ledger_id):
    head_hashes = set([n.getState(ledger_id).headHash for n in node_set])
    assert len(head_hashes) == 1
    return head_hashes.pop()


def get_committed_hash_for_pool(node_set, ledger_id):
    head_hashes = set([n.getState(ledger_id).committedHeadHash for n in node_set])
    assert len(head_hashes) == 1
    return head_hashes.pop()


def get_committed_txn_root_for_pool(node_set, ledger_id):
    hashes = set([n.getLedger(ledger_id).tree.root_hash for n in node_set])
    assert len(hashes) == 1
    return hashes.pop()


def get_uncommitted_txn_root_for_pool(node_set, ledger_id):
    hashes = set([n.getLedger(ledger_id).uncommitted_root_hash for n in node_set])
    assert len(hashes) == 1
    return hashes.pop()


def sdk_send_new_nym(looper, sdk_pool_handle, creators_wallet,
                     alias=None, role=None, seed=None,
                     dest=None, verkey=None, skipverkey=False):
    seed = seed or randomString(32)
    alias = alias or randomString(5)
    wh, _ = creators_wallet

    # filling nym request and getting steward did
    # if role == None, we are adding client
    nym_request, new_did = looper.loop.run_until_complete(
        prepare_nym_request(creators_wallet, seed,
                            alias, role, dest, verkey, skipverkey))

    # sending request using 'sdk_' functions
    signed_reqs = sdk_sign_request_objects(looper, creators_wallet,
                                           [sdk_json_to_request_object(
                                               json.loads(nym_request))])
    request_couple = sdk_send_signed_requests(sdk_pool_handle, signed_reqs)
    return request_couple


def nyms_with_fees(req_count,
                   helpers,
                   fees_set,
                   address_main,
                   all_amount,
                   init_seq_no):
    amount = all_amount
    seq_no = init_seq_no
    fee_amount = fees_set[FEES].get(NYM_FEES_ALIAS, 0)
    reqs = []
    for i in range(req_count):
        req = helpers.request.nym()
        if fee_amount:
            utxos = [{"source": utxo_from_addr_and_seq_no(address_main, seq_no),
                      AMOUNT: amount}]
            req = add_fees_request_with_address(
                helpers,
                fees_set,
                req,
                address_main,
                utxos=utxos
            )
            seq_no += 1
            amount -= fee_amount
        reqs.append(req)
    return reqs


def send_and_check_nym_with_fees(helpers, fees_set, seq_no, looper, addresses, current_amount,
                                 check_reply=True, nym_with_fees=None):
    if not nym_with_fees:
        nym_with_fees = nyms_with_fees(1,
                                       helpers,
                                       fees_set,
                                       addresses[0],
                                       current_amount,
                                       init_seq_no=seq_no)[0]
    resp = helpers.sdk.send_request_objects([nym_with_fees])

    if check_reply:
        sdk_get_and_check_replies(looper, resp)

    current_amount -= fees_set[FEES].get(NYM_FEES_ALIAS, 0)
    seq_no += 1 if fees_set[FEES].get(NYM_FEES_ALIAS, 0) else 0
    return current_amount, seq_no, resp


def send_and_check_transfer(helpers, addresses, fees, looper, current_amount,
                            seq_no, check_reply=True, transfer_summ=20):
    [address_giver, address_receiver] = addresses
    if transfer_summ == current_amount:
        outputs = [{ADDRESS: address_receiver, AMOUNT: transfer_summ - fees.get(XFER_PUBLIC_FEES_ALIAS, 0)}]
        new_amount = transfer_summ - fees.get(XFER_PUBLIC_FEES_ALIAS, 0)
    else:
        outputs = [{ADDRESS: address_receiver, AMOUNT: transfer_summ},
                   {ADDRESS: address_giver, AMOUNT: current_amount - transfer_summ - fees.get(XFER_PUBLIC_FEES_ALIAS, 0)}]
        new_amount = current_amount - (fees.get(XFER_PUBLIC_FEES_ALIAS, 0) + transfer_summ)

    inputs = [{"source": utxo_from_addr_and_seq_no(address_giver, seq_no)}]
    transfer_req = helpers.request.transfer(inputs, outputs)

    resp = helpers.sdk.send_request_objects([transfer_req])
    if check_reply:
        sdk_get_and_check_replies(looper, resp)

    seq_no += 1
    return new_amount, seq_no, resp


def prepare_inputs(
    helpers, addresses, strategy=InputsStrategy.all_utxos
):
    assert strategy in InputsStrategy, "Unknown input strategy {}".format(strategy)

    inputs = []
    addresses = [helpers.wallet.address_map[addr.replace("pay:sov:", "")] for addr in addresses]
    for addr in addresses:
        if not addr.all_seq_nos:
            raise ValueError("no seq_nos for {}".format(addr.address))
        for seq_no in addr.all_seq_nos:
            inputs.append({"source": utxo_from_addr_and_seq_no(addr.address, seq_no), ADDRESS: addr.address, SEQNO: seq_no})
            if strategy == InputsStrategy.first_utxo_only:
                break

    return inputs


def prepare_outputs(
    helpers, fee, inputs, addresses,
    strategy=OutputsStrategy.transfer_some_equal, transfer_amount=20
):
    def divide_equal(output_addresses, amount):
        output_amount = amount // len(output_addresses)
        assert output_amount > 0
        res = {addr: output_amount for addr in output_addresses}
        res[output_addresses[-1]] += amount % len(output_addresses)
        return res

    assert strategy in OutputsStrategy, "Unknown output strategy {}".format(strategy)

    total_input_amount = sum(
        (helpers.wallet.address_map[i[ADDRESS].replace("pay:sov:", "")].amount(i[SEQNO]) for i in inputs)
    )

    # apply fee
    total_output_amount = total_input_amount - fee

    if strategy == OutputsStrategy.transfer_all_equal:
        transfer_amount = total_output_amount
        strategy = OutputsStrategy.transfer_some_equal

    assert transfer_amount >= 0

    change = total_output_amount - transfer_amount
    # we have enough input amount
    assert change >= 0

    # transfer is divided among outputs
    if transfer_amount:
        outputs = divide_equal(addresses, transfer_amount)
    else:
        outputs = {}

    # change goes to any input presented in outputs as well or first input address
    if change:
        both_io_addrs = list(set([i[ADDRESS] for i in inputs]) & set(addresses))
        change_addr = both_io_addrs[0] if both_io_addrs else inputs[0][ADDRESS]

        if change_addr not in outputs:
            outputs[change_addr] = 0

        outputs[change_addr] += change

    return [{ADDRESS: addr, AMOUNT: amount} for addr, amount in outputs.items()]


def send_and_check_xfer(looper, helpers, inputs, outputs):
    resp = helpers.sdk.get_first_result(
        helpers.sdk.send_and_check_request_objects([
            helpers.request.transfer(inputs, outputs)
        ])
    )
    helpers.wallet.handle_xfer(resp)
    return resp


def send_and_check_nym(looper, helpers, inputs, outputs):
    resp = helpers.sdk.get_first_result(
        helpers.sdk.sdk_send_and_check([
            helpers.request.add_fees_specific(
                helpers.request.nym(), inputs, outputs
            )[0]
        ])
    )
    helpers.wallet.handle_txn_with_fees(resp)
    return resp


def ensure_all_nodes_have_same_data(looper, node_set, custom_timeout=None,
                                    exclude_from_check=None):
    waitNodeDataEquality(looper, node_set[0], *node_set[1:],
                         customTimeout=custom_timeout,
                         exclude_from_check=exclude_from_check)

    def chk_utxo_cache(node, nodes):
        cache = {}
        utxo_data = {}
        for n in nodes:
            cache[n.name] = {}
            utxo_data[n.name] = {}
            cache_storage = n.ledger_to_req_handler[TOKEN_LEDGER_ID].utxo_cache._store
            for key, value in cache_storage.iterator(include_value=True):
                cache[n.name][key] = value
                utxo_data[n.name] = UTXOAmounts.get_amounts(key, n.ledger_to_req_handler[TOKEN_LEDGER_ID].utxo_cache,
                                                            is_committed=True).as_str()
        assert all(cache[node.name] == cache[n.name] for n in nodes)
        assert all(utxo_data[node.name] == utxo_data[n.name] for n in nodes)
        print(cache)
        print(utxo_data)

    looper.run(eventually(chk_utxo_cache, node_set[0], node_set))
