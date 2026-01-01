# Module 8: Microservices Design Patterns

## Objectives

After completing this module, you will:
- Design service boundaries and decomposition strategies
- Implement API gateway patterns
- Handle distributed data and service contracts
- Version APIs and manage backward compatibility
- Design cross-service communication
- Implement service mesh patterns (sidecars)

## 8.1 Service Boundaries

Critical decision: where to split the monolith?

### Domain-Driven Design (DDD)

```
Large system decomposed by business domains:

E-commerce Platform:
├─ User Service: profiles, authentication, preferences
├─ Catalog Service: products, categories, search
├─ Order Service: order creation, fulfillment
├─ Payment Service: payment processing
├─ Inventory Service: stock management
├─ Shipping Service: delivery logistics
└─ Review Service: ratings, reviews

Boundary: Each service owns its domain
- User Service owns user data (other services get user data via API)
- Order Service owns order data
- No direct database access between services (API only)

Benefit:
- Clear ownership
- Independent deployment
- Technology diversity (if needed)
```

### Service Decomposition Anti-Patterns

**Wrong**: Decompose by layer
```
❌ UserController Service
❌ UserRepository Service  
❌ UserDomain Service

Problem: Tight coupling, requires calls to all 3 for single operation
```

**Wrong**: Decompose by technology
```
❌ CacheService
❌ DatabaseService
❌ MessageQueueService

Problem: Infrastructure, not business logic
```

**Right**: Decompose by business capability
```
✓ UserService (owns everything user-related)
✓ OrderService (owns everything order-related)
✓ PaymentService (owns payment logic)

Problem: Each service might have cache, DB, queue (duplicated infra)
Solution: That's OK, each service independently scalable
```

## 8.2 API Gateway Pattern

Single entry point for all client requests:

```
Clients (Web, Mobile, Desktop)
  ↓
API Gateway
├─ Authentication
├─ Rate limiting
├─ Request routing
├─ Response aggregation
  ↓
├─ User Service
├─ Order Service
├─ Product Service
├─ Payment Service
└─ etc.
```

### API Gateway Responsibilities

```
1. Request Routing
   GET /api/users/123 → UserService
   GET /api/orders/456 → OrderService

2. Authentication
   Verify JWT token before forwarding request

3. Rate Limiting
   Per-user limits (prevent abuse)

4. Protocol Translation
   HTTP/REST → gRPC → internal services

5. Response Aggregation
   GET /api/orders/123 (includes user + items)
   ├─ Fetch from OrderService
   ├─ Fetch from UserService
   └─ Combine responses

6. Caching
   Cache frequently accessed endpoints

7. Circuit Breaking
   If OrderService down, return error without trying all requests
```

### Implementation

```python
from flask import Flask, jsonify
import requests

app = Flask(__name__)

SERVICES = {
    'users': 'http://user-service:8000',
    'orders': 'http://order-service:8000',
    'products': 'http://product-service:8000',
}

@app.route('/api/orders/<order_id>')
def get_order(order_id):
    # Fetch order
    order = requests.get(f"{SERVICES['orders']}/orders/{order_id}").json()
    
    # Fetch user details
    user = requests.get(f"{SERVICES['users']}/users/{order['user_id']}").json()
    
    # Combine
    return jsonify({
        'order': order,
        'user': user
    })
```

## 8.3 Inter-Service Communication

How services talk to each other:

### Synchronous (REST/gRPC)

```
Service A                Service B
    ↓
    HTTP Request (REST)
    ├─ Blocking wait
    └─ Response
    ↓
Continue with response

Advantages: Simple, immediate feedback
Disadvantages: Coupling, cascading failures
```

### Asynchronous (Message Queue)

```
Service A                   Queue                Service B
    ↓
    Publish event
    ├─ Continue immediately (don't wait)
    ↓
    (Queue holds message)
                               ↓
                           Service B reads
                           (might be seconds later)
                           ↓
                           Process event

Advantages: Decoupling, resilience
Disadvantages: Complexity, eventual consistency
```

### Choosing Communication Pattern

```
Critical path (must return immediately):
├─ User login
├─ Payment processing
├─ Inventory check
└─ Use: Synchronous (REST/gRPC)

Non-critical path (can be eventual):
├─ Send email confirmation
├─ Update analytics
├─ Update recommendations
├─ Send notifications
└─ Use: Asynchronous (message queue)

Hybrid: Synchronous for critical path, async for rest
```

## 8.4 API Versioning and Contracts

Services evolve, compatibility is critical.

### Versioning Strategy

```
Option 1: URL Versioning
GET /api/v1/orders/123
GET /api/v2/orders/123 (different response format)

Option 2: Header Versioning
GET /api/orders/123
Header: Api-Version: 1 or Api-Version: 2

Option 3: Content Negotiation
GET /api/orders/123
Header: Accept: application/vnd.mycompany.v2+json
```

### Backward Compatibility

```
Version 1 response:
{
  "order_id": 123,
  "amount": 99.99
}

Version 2 adds field:
{
  "order_id": 123,
  "amount": 99.99,
  "currency": "USD"  // New field
}

Backward compatibility:
Old clients ignore 'currency' (safe)
New clients handle both versions

Breaking changes (avoid):
Removing fields
Changing field types
Changing semantics
```

### Contract-Driven Development

```
Service Contract:

POST /api/orders
Request:
{
  "user_id": int,
  "items": [{id: int, quantity: int}],
  "shipping_address": string
}

Response (201):
{
  "order_id": int,
  "status": "pending",
  "created_at": timestamp
}

Error (400):
{
  "error": "invalid_items",
  "message": "Item 999 not found"
}

Contract (don't change without coordination):
- Required fields must stay
- Add optional fields (backward compatible)
- Error response structure
- Status codes
```

## 8.5 Handling Distributed Data

Data is split across services, no single source of truth.

### Data Consistency Patterns

```
Pattern 1: API Composition (read-time join)
Order Service: Has order
User Service: Has user data
API Gateway: Calls both, combines response

Pattern 2: Event-Based Replication (eventual consistency)
Order Service: Creates order, publishes "OrderCreated"
Cache: Subscribes, maintains denormalized copy
Cache hits: 1ms latency, might be 1 second stale

Pattern 3: Saga Pattern (distributed transaction)
Order Service: Create order
Inventory Service: Reserve stock
Payment Service: Process payment
(As discussed in Module 7)
```

### Service Ownership

```
Every piece of data owned by one service:

User Data:
├─ Owned by: User Service
├─ Other services: Call API or cache copies
├─ Other services: NEVER write user data
└─ Rule: Single writer pattern

Order Data:
├─ Owned by: Order Service
├─ Other services: Call API or subscribe to events
└─ Other services: NEVER write order data

Benefit: Clear ownership, no conflicts
Cost: Must call APIs or use events to access data
```

## 8.6 Service Mesh and Sidecars

Infrastructure layer handling inter-service communication:

### Sidecar Pattern

```
Without sidecar:
Service A
├─ App code
├─ RPC client code
├─ Circuit breaker code
├─ Retry logic
├─ Rate limiting code
├─ Tracing code
└─ (Lots of complex infra code)

With sidecar:
Service A                  Envoy Sidecar
├─ App code            ├─ RPC client code
├─ Logic only          ├─ Circuit breaker
└─ Business logic      ├─ Retry logic
  ↓                    ├─ Rate limiting
  (localhost:9001)     ├─ Tracing
                       └─ Infrastructure
  ↓
  (delegates to sidecar)

Benefit: Separate concerns
- App: business logic
- Sidecar: infrastructure concerns
```

### Kubernetes/Envoy Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: order-service-pod
spec:
  containers:
  - name: order-service
    image: order-service:v1.0
    ports:
    - containerPort: 8080
  
  - name: envoy-proxy (sidecar)
    image: envoyproxy/envoy:v1.20
    ports:
    - containerPort: 10000
```

## 8.7 Production Recommendations

### Service Size

Microservice should be:
- Small enough for one team to understand
- Large enough to be deployed independently
- Not so small that coordination overhead exceeds benefit

### Fault Isolation

Each service failure should affect only that service:
- User Service down → can't login, but can still browse
- Order Service down → can't order, but can see products
- Payment Service down → can't complete order, but can create pending

Never: "One service down → entire system unusable"

### Observability

Each service must be observable:
- Structured logging
- Distributed tracing
- Metrics collection
- Health checks

---

## Exam & Practice

### Multiple Choice Questions

**Q1**: How should services share data?

A) Direct database access
B) Service-to-service APIs
C) Shared cache
D) All of above

**Q2**: Service A depends on Service B. Service B becomes slow (5s latency). What happens without circuit breaker?

A) Service A remains fast (other requests)
B) Service A threads fill up waiting for B
C) Cascading failure
D) Service A times out, retries

**Q3**: You want to add a new field to Order response. How to maintain backward compatibility?

A) Remove old field
B) Add new field, keep old field
C) Change all clients first
D) Create new API version

**Q4**: Should sidecar handle business logic?

A) Yes (simplifies service)
B) No (infrastructure only)
C) Maybe (depends on logic)
D) Only critical logic

**Q5**: Service owns order data. Another service needs order total. What's correct approach?

A) Other service reads order database
B) Other service calls Order Service API
C) Other service receives via event
D) B or C

### Hands-on Tasks

**Task 1: Microservice Decomposition**

Break down an e-commerce monolith into services:
- Current monolith: 50K lines of code
- Functions: users, products, orders, payments, inventory, reviews, recommendations

Design:
- Service boundaries
- Data ownership
- Communication patterns (sync vs async)
- Shared vs separated infrastructure

**Task 2: API Gateway Design**

Design API gateway for microservices:
- Should handle: auth, rate limiting, logging, tracing
- Route requests to appropriate services
- Handle failures gracefully

Specify:
- Architecture
- How to handle service discovery
- How to aggregate data from multiple services

### Incident Scenario

**Scenario: Cascading Failure from Service Dependency**

Timeline:
- T+0: Payment Service latency increases (normally 50ms, now 2s)
- T+5min: Order Service calls Payment Service (expecting 50ms, waits 2s)
- T+6min: Order Service threads fill up (each waiting on Payment)
- T+7min: Order Service can't accept new requests (all threads busy)
- T+10min: API Gateway times out calling Order Service
- T+12min: Entire order flow fails
- T+25min: Team discovers Payment Service is slow
- T+30min: Payment Service restarted

**Questions:**
1. How would circuit breaker help?
2. How would timeouts/bulkheads help?
3. What monitoring would catch this at T+5min?
4. Should Order Service always call Payment Service synchronously?
5. Design alternative: async payment processing

---

**Next**: [Module 9: Observability in Distributed Systems](09-observability.md)
