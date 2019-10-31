from typing import List, Union

from .keypair import Keypair
from .memo import NoneMemo, Memo
from .operation.operation import Operation
from .xdr import Xdr
from .strkey import StrKey
from .time_bounds import TimeBounds
from .utils import pack_xdr_array, unpack_xdr_array

__all__ = ["Transaction"]


class Transaction:
    """The :class:`Transaction` object, which represents a transaction
    on Stellar's network.

    A transaction contains a list of operations, which are all executed
    in order as one ACID transaction, along with an
    associated source account, fee, account sequence number, list of
    signatures, both an optional memo and an optional TimeBounds. Typically a
    :class:`Transaction` is placed in a :class:`TransactionEnvelope
    <stellar_sdk.transaction_envelope.TransactionEnvelope>` which is
    then signed before being sent over the network.

    For more information on Transactions in Stellar, see `Stellar's guide
    on transactions`_.

    .. _Stellar's guide on transactions:
        https://www.stellar.org/developers/guides/concepts/transactions.html

    :param source: the source account for the transaction.
    :param sequence: The sequence number for the transaction.
    :param fee: The fee amount for the transaction, which should equal
          FEE (currently 100 stroops) multiplied by the number of
          operations in the transaction. See `Stellar's latest documentation
          on fees
          <https://www.stellar.org/developers/guides/concepts/fees.html#transaction-fee>`_
          for more information.
    :param operations: A list of operations objects (typically its
          subclasses as defined in :mod:`stellar_sdk.operation.Operation`.
    :param time_bounds: The timebounds for the validity of this transaction.
    :param memo: The memo being sent with the transaction, being
          represented as one of the subclasses of the
          :class:`Memo <stellar_sdk.memo.Memo>` object.
    """

    def __init__(
        self,
        source: Keypair,
        sequence: int,
        fee: int,
        operations: List[Operation],
        memo: Memo = None,
        time_bounds: TimeBounds = None,
    ) -> None:

        # if not operations:
        #     raise ValueError("At least one operation required.")

        if memo is None:
            memo = NoneMemo()

        self.source: Keypair = source
        self.sequence: int = sequence
        self.operations: List[Operation] = operations
        self.memo: Memo = memo
        self.fee: int = fee
        self.time_bounds: TimeBounds = time_bounds

    def to_xdr_object(self) -> Xdr.types.Transaction:
        """Get an XDR object representation of this :class:`Transaction`.

        :return: XDR Transaction object
        """
        source_account = self.source.xdr_account_id()
        memo = self.memo.to_xdr_object()
        operations = [operation.to_xdr_object() for operation in self.operations]
        time_bounds: List[TimeBounds] = []
        if self.time_bounds:
            time_bounds = pack_xdr_array(self.time_bounds.to_xdr_object())
        ext = Xdr.nullclass()
        ext.v = 0
        return Xdr.types.Transaction(
            source_account, self.fee, self.sequence, time_bounds, memo, operations, ext
        )

    @classmethod
    def from_xdr_object(cls, tx_xdr_object) -> "Transaction":
        """Create a new :class:`Transaction` from an XDR object.

        :param tx_xdr_object: The XDR object that represents a transaction.

        :return: A new :class:`Transaction` object from the given XDR Transaction object.
        """
        source = Keypair.from_public_key(
            StrKey.encode_ed25519_public_key(tx_xdr_object.sourceAccount.ed25519)
        )
        sequence = tx_xdr_object.seqNum
        fee = tx_xdr_object.fee
        time_bounds_in_xdr = tx_xdr_object.timeBounds
        time_bounds = None
        if time_bounds_in_xdr:
            time_bounds = TimeBounds.from_xdr_object(
                unpack_xdr_array(time_bounds_in_xdr)
            )

        memo = Memo.from_xdr_object(tx_xdr_object.memo)
        operations = list(map(Operation.from_xdr_object, tx_xdr_object.operations))
        return cls(
            source=source,
            sequence=sequence,
            time_bounds=time_bounds,
            memo=memo,
            fee=fee,
            operations=operations,
        )
