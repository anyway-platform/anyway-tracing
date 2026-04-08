from enum import Enum
from typing import Sequence
from anyway.sdk.tracing.tracing import set_association_properties


class AssociationProperty(str, Enum):
    """Standard association properties for tracing.

    Use these with set_association_properties() or decorator association_properties config.

    Set customer and session context::

        Traceloop.set_association_properties({
            AssociationProperty.CUSTOMER_ID: "CUS_a1b2c3d4e5f6",
            AssociationProperty.SESSION_ID: "session-abc",
        })

    Add order context::

        Traceloop.set_association_properties({
            AssociationProperty.USER_ID: "user-123",
            AssociationProperty.CUSTOMER_ID: "CUS_a1b2c3d4e5f6",
            AssociationProperty.ORDER_ID: "ORD_x7y8z9",
        })
    """

    #: Anyway platform customer identifier (CUS_xxx format).
    #: Obtained from the Anyway Customers API or order system.
    #: Use this to link traces to Anyway billing, orders, and revenue attribution.
    CUSTOMER_ID = "customer_id"
    #: Your application's internal user identifier (from your own auth system).
    #: Use this to filter and group traces by user in your app.
    USER_ID = "user_id"
    #: A session or conversation identifier. Use this to correlate traces within a single session.
    SESSION_ID = "session_id"
    #: An order or transaction identifier. Use this to trace a specific business transaction.
    ORDER_ID = "order_id"


# Type alias for a single association
Association = tuple[AssociationProperty, str]


class Associations:
    """Class for managing trace associations."""

    @staticmethod
    def set(associations: Sequence[Association]) -> None:
        """
        Set associations that will be added directly to all spans in the current context.

        Args:
            associations: A sequence of (property, value) tuples

        Example:
            # Single association
            traceloop.associations.set([(AssociationProperty.SESSION_ID, "conv-123")])

            # Multiple associations
            traceloop.associations.set([
                (AssociationProperty.USER_ID, "user-456"),
                (AssociationProperty.SESSION_ID, "session-789")
            ])
        """
        # Convert associations to a dict and use set_association_properties
        properties = {prop.value: value for prop, value in associations}
        set_association_properties(properties)
