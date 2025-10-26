package com.example.softwareQuality.automation;

import io.cucumber.java.Before;
import io.cucumber.java.BeforeStep;
import io.cucumber.java.Scenario;
import io.cucumber.java.en.And;
import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

public class ShipmentSteps {
    private final TestContext context;

    public ShipmentSteps(TestContext context) {
        this.context = context;
    }

    @Before
    public void beforeScenario() {
        // ensure fresh maps per scenario
        context.put("orders", new HashMap<String, Map<String, Object>>());
        context.put("shipments", new HashMap<String, Map<String, Object>>());
        context.put("carriers", new HashMap<String, Boolean>());
    }

    @Given("the system is available")
    public void systemIsAvailable() {
        context.put("systemAvailable", true);
    }

    @Given("a customer places an order with id {string} and destination {string}")
    public void customerPlacesOrder(String orderId, String destination) {
        Map<String, Map<String, Object>> orders = context.get("orders", Map.class);
        Map<String, Object> order = new HashMap<>();
        order.put("id", orderId);
        order.put("destination", destination);
        order.put("state", "ORDER_PLACED");
        orders.put(orderId, order);
        context.put("lastOrderId", orderId);
    }

    @And("the system allocates a shipment with carrier {string} and service {string}")
    public void systemAllocatesShipment(String carrier, String service) {
        String orderId = context.get("lastOrderId", String.class);
        assertNotNull(orderId, "No order in context to allocate shipment for");

        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        Map<String, Object> shipment = new HashMap<>();
        shipment.put("orderId", orderId);
        shipment.put("carrier", carrier);
        shipment.put("service", service);
        shipment.put("state", "ALLOCATED");
        // no tracking assigned yet
        shipments.put(orderId, shipment); // temporarily key by orderId until tracking provided
    }

    @When("the carrier picks up the shipment with tracking {string}")
    public void carrierPicksUpShipment(String trackingId) {
        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        // if a shipment exists keyed by orderId, move it under trackingId
        String orderId = context.get("lastOrderId", String.class);
        Map<String, Object> shipment = shipments.get(orderId);
        if (shipment == null) {
            // perhaps test provided tracking first — create a minimal shipment
            shipment = new HashMap<>();
            shipment.put("orderId", orderId);
            shipment.put("carrier", "UNKNOWN");
            shipment.put("service", "UNKNOWN");
            shipment.put("state", "ALLOCATED");
        }
        shipment.put("trackingId", trackingId);
        shipment.put("state", "PICKED_UP");
        // rekey by trackingId
        shipments.put(trackingId, shipment);
        // remove old orderId key if present
        shipments.remove(orderId);
    }

    @And("the carrier updates the shipment status to {string}")
    public void carrierUpdatesStatus(String status) {
        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        // find the only shipment in map (or the one with last known tracking)
        String tracking = findAnyTracking(shipments);
        assertNotNull(tracking, "No shipment found to update");
        Map<String, Object> shipment = shipments.get(tracking);
        shipment.put("state", status);
    }

    @Then("the shipment for order {string} should be marked as {string}")
    public void shipmentShouldBeMarked(String orderId, String expectedState) {
        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        // try to find shipment by tracking or orderId
        Map<String, Object> found = null;
        for (Map.Entry<String, Map<String, Object>> e : shipments.entrySet()) {
            Map<String, Object> s = e.getValue();
            if (orderId.equals(s.get("orderId"))) {
                found = s;
                break;
            }
        }
        assertNotNull(found, "Shipment for order " + orderId + " not found");
        assertEquals(expectedState, found.get("state"));
    }

    @Given("the primary carrier {string} is unavailable")
    public void primaryCarrierUnavailable(String carrier) {
        Map<String, Boolean> carriers = context.get("carriers", Map.class);
        carriers.put(carrier, false);
    }

    @When("the system reassigns the shipment to a backup carrier {string}")
    public void systemReassignsToBackup(String backupCarrier) {
        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        String orderId = context.get("lastOrderId", String.class);
        // find shipment for order
        Map<String, Object> found = null;
        for (Map.Entry<String, Map<String, Object>> e : shipments.entrySet()) {
            Map<String, Object> s = e.getValue();
            if (orderId.equals(s.get("orderId"))) {
                found = s;
                break;
            }
        }
        if (found == null) {
            // create one if missing
            found = new HashMap<>();
            found.put("orderId", orderId);
            found.put("state", "ALLOCATED");
            shipments.put(orderId, found);
        }
        found.put("carrier", backupCarrier);
        found.put("reassigned", true);
    }

    @Then("the shipment should be assigned to {string}")
    public void shipmentShouldBeAssignedTo(String expectedCarrier) {
        Map<String, Map<String, Object>> shipments = context.get("shipments", Map.class);
        String orderId = context.get("lastOrderId", String.class);
        Map<String, Object> found = null;
        for (Map.Entry<String, Map<String, Object>> e : shipments.entrySet()) {
            Map<String, Object> s = e.getValue();
            if (orderId.equals(s.get("orderId"))) {
                found = s;
                break;
            }
        }
        assertNotNull(found, "Shipment not found for order " + orderId);
        assertEquals(expectedCarrier, found.get("carrier"));
    }

    // helper to find any tracking key
    private String findAnyTracking(Map<String, Map<String, Object>> shipments) {
        for (Map.Entry<String, Map<String, Object>> e : shipments.entrySet()) {
            Map<String, Object> s = e.getValue();
            if (s.containsKey("trackingId")) {
                return (String) s.get("trackingId");
            }
        }
        // fallback to first key
        return shipments.keySet().stream().findFirst().orElse(null);
    }

    @Given("business step {string}")
    public void business_step(String string) {
        // Write code here that turns the phrase above into concrete actions
        //throw new io.cucumber.java.PendingException();
    }
}

