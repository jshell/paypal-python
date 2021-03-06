# coding=utf-8
"""
PayPalResponse parsing and processing.

Updated 2015-04-15 Jeffrey Shell: Changed PayPalResponse to be based on
    abstract base class :class:`collections.Mapping` and to ensure that
    `getattr` indicated the attribute name when raising AttributeError.
    There are so many response values that are optional that its helpful
    to know what is missing, or to use convenience methods like `.get`.
"""

import logging
from collections import Mapping
from pprint import pformat

from paypal.compat import is_py3

if is_py3:
    #noinspection PyUnresolvedReferences
    from urllib.parse import parse_qs
else:
    # Python 2.6 and up (but not 3.0) have urlparse.parse_qs, which is copied
    # from Python 2.5's cgi.parse_qs.
    from urlparse import parse_qs

logger = logging.getLogger('paypal.response')


class PayPalResponse(Mapping):
    """
    Parse and prepare the reponse from PayPal's API. Acts as a read-only
    dictionary that does the following:

    * Supports getting keys by upper or lower case (the raw response is all
      upper case).
    * Turns single-list-item values in the parsed response into Scalars
      (in raw response, all values are lists).
    * Provides attribute access to the response keys.
    """
    def __init__(self, query_string, config):
        """
        query_string is the response from the API, in NVP format. This is
        parseable by urlparse.parse_qs(), which sticks it into the
        :attr:`raw` dict for retrieval by the user.

        :param str query_string: The raw response from the API server.
        :param PayPalConfig config: The config object that was used to send
            the query that caused this response.
        """
        # A dict of NVP values. Don't access this directly, use
        # PayPalResponse.attribname instead. See self.__getattr__().
        self.raw = parse_qs(query_string)
        self.config = config
        logger.debug("PayPal NVP API Response:\n%s" % self.__str__())

    def __str__(self):
        """
        Returns a string representation of the raw PayPalResponse object, in
        'pretty-print' format.

        :rtype: str
        :returns: A 'pretty' string representation of the response dict.
        """
        return pformat(dict(self.items()))

    def formatted(self):
        """
        Returns a formatted string representation of the response dictionary
        with values flattened.
        """
        return pformat(dict(self.items()))

    def __repr__(self):
        return '<{module}.{classname} {items!r}>'.format(
            module=self.__module__, classname=self.__class__.__name__,
            items=dict(self.items()),
        )

    def __getattr__(self, key):
        """
        Handles the retrieval of attributes that don't exist on the object
        already. This is used to get API response values. Handles some
        convenience stuff like discarding case and checking the cgi/urlparsed
        response value dict (self.raw).

        :param str key: The response attribute to get a value for.
        :rtype: str
        :returns: The requested value from the API server's response.
        """
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    ## collections.Mapping just needs getitem, iter, and len support.
    def __getitem__(self, key):
        """
        Another (dict-style) means of accessing response data.

        :param str key: The response key to get a value for.
        :rtype: str
        :returns: The requested value from the API server's response.
        """
        # PayPal response names are always uppercase.
        key = key.upper()
        value = self.raw[key]
        if len(value) == 1:
            # For some reason, PayPal returns lists for all of the values.
            # I'm not positive as to why, so we'll just take the first
            # of each one. Hasn't failed us so far.
            return value[0]
        return value

    def __iter__(self):
        return iter(self.raw)

    def __len__(self):
        return len(self.raw)

    @property
    def success(self):
        """
        Checks for the presence of errors in the response. Returns ``True`` if
        all is well, ``False`` otherwise.

        :rtype: bool
        :returns ``True`` if PayPal says our query was successful.
        """
        return self.ack.upper() in (self.config.ACK_SUCCESS,
                                    self.config.ACK_SUCCESS_WITH_WARNING)
