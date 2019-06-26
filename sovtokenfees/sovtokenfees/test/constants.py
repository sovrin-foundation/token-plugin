from indy_common.constants import NYM, ATTRIB, SCHEMA, CLAIM_DEF
from sovtoken.constants import XFER_PUBLIC

NYM_FEES_ALIAS = 'nym_fees_alias'
XFER_PUBLIC_FEES_ALIAS = 'xfer_public_fees_alias'
NODE_FEES_ALIAS = 'node_fees_alias'
ATTRIB_FEES_ALIAS = 'attrib_fees_alias'
SCHEMA_FEES_ALIAS = 'schema_fees_alias'
CLAIM_DEF_FEES_ALIAS = 'claim_def_fees_alias'
REVOC_REG_DEF_FEES_ALIAS = "revoc_reg_def_fees_alias"
REVOC_REG_ENTRY_FEES_ALIAS = "revoc_reg_entry_fees_alias"


txn_type_to_alias = {
    NYM: NYM_FEES_ALIAS,
    XFER_PUBLIC: XFER_PUBLIC_FEES_ALIAS,
    ATTRIB: ATTRIB_FEES_ALIAS,
    SCHEMA: SCHEMA_FEES_ALIAS,
    CLAIM_DEF: CLAIM_DEF_FEES_ALIAS
}

alias_to_txn_type = {
    NYM_FEES_ALIAS: NYM,
    XFER_PUBLIC_FEES_ALIAS: XFER_PUBLIC,
    ATTRIB_FEES_ALIAS: ATTRIB,
    SCHEMA_FEES_ALIAS: SCHEMA,
    CLAIM_DEF_FEES_ALIAS: CLAIM_DEF,
}