from common.serializers.base58_serializer import Base58Serializer
from common.serializers.serialization import state_roots_serializer as pstate_serializer, \
                                             proof_nodes_serializer as pproof_nodes_serializer, \
                                             config_state_serializer as pconfig_state_serializer

txn_root_serializer = Base58Serializer()

state_roots_serializer = pstate_serializer
proof_nodes_serializer = pproof_nodes_serializer
config_state_serializer = pconfig_state_serializer
