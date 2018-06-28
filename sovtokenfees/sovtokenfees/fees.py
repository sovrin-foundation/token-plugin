class FeesPlugin:
    def __init__(self, token_bank, **kwargs):
        pass

    def validate(self, txn):
        # Calls `can_pay_fees` to find out if the txn is valid
        pass

    def apply(self, txn):
        # Calls `deduct_fees` to charge the sender of the txn
        pass

    def get_fees(self, txn):
        # This needs to be overridden
        pass

    def can_pay_fees(self, txn):
        # Check if the txn inputs are paying the required sovtokenfees to "sink address"
        # . Needs to call TokenPlugin's `is_valid_tranfer` method
        pass

    def deduct_fees(self, txn):
        # Deduct sovtokenfees if possible else raise exception InsufficientFunds.
        # Needs to call TokenPlugin's `do_transfer` method
        pass
