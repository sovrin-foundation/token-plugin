from sovtokenfees.constants import FEES_KEY_DELIMITER, FEES_STATE_PREFIX, FEES_KEY_FOR_ALL


def build_path_for_set_fees(alias=None):
    if alias:
        return FEES_KEY_DELIMITER.join([FEES_STATE_PREFIX, alias])
    return FEES_KEY_DELIMITER.join([FEES_STATE_PREFIX, FEES_KEY_FOR_ALL])