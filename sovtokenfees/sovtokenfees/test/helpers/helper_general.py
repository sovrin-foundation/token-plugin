import sovtoken.test.helpers.helper_general as token_helper_general


class HelperGeneral(token_helper_general.HelperGeneral):
    """
    Extends the sovtoken HelperGeneral with fee related methods.

    # Methods
    - do_get_fees
    """

    def do_get_fees():
        """ Builds and sends a get_fees request """
        request = self._request.get_fees()
        return self._send_get_first_result(request)
