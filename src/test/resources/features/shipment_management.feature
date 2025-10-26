Feature: Shipment Management
  Verify end-to-end shipment creation and delivery processes for different carriers and shipment types.

  @mermaid @bpt
  Scenario Outline: Create and complete a shipment
    * business step "📦 Check pre-requisite"
    Given the system is available
    * business step "🧾 Parcel Registration"
    Given a customer places an order with id "<orderId>" and destination "<destination>"
    * business step "🚚📍 Parcel pickup"
    And the system allocates a shipment with carrier "<carrier>" and service "<service>"
    Then the shipment for order "<orderId>" should be marked as "<expectedState>"
    When the carrier picks up the shipment with tracking "<trackingId>"
    * business step "🚚➡️🏬 Parcel In Transit"
    And the carrier updates the shipment status to "<status>"
    Then the shipment for order "<orderId>" should be marked as "<expectedState>"

    Examples:
      | orderId  | destination     | carrier    | service    | trackingId   | status     | expectedState |
      | ORD-1001 | New York, NY    | FastShip   | Express    | TRK1001      | IN_TRANSIT | In Transit    |
      | ORD-1002 | Los Angeles, CA | National   | Standard   | TRK1002      | DELIVERED  | Delivered     |

  Scenario: Failover when primary carrier unavailable
    Given the system is available
    Given a customer places an order with id "ORD-2001" and destination "Chicago, IL"
    And the primary carrier "PrimaryCo" is unavailable
    When the system reassigns the shipment to a backup carrier "BackupCo"
    Then the shipment should be assigned to "BackupCo"

