# Multi-stop routing

`RoutingProvider` defines route, matrix and multi-stop optimization operations; fixture and unavailable adapters exist. The core does not hardcode a commercial maps vendor. No real provider credentials or road-network engine are configured in this environment. Multi-order batching, capacity/food compatibility, stop sequencing and route geometry are not production-enabled. Tasks remain separate per fulfillment unit and scheduled windows remain separate; proximity alone never merges deliveries.
