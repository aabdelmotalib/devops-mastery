# Module 3: REST API Design

## What REST Actually Means

REST = Representational State Transfer

But forget the acronym. Think practically:

**REST is a way to structure your API so it's predictable and scalable.**

### The Core Idea

Instead of:

```
POST /createUser
POST /deleteUser
POST /updateUser
GET /getUser
POST /getUserList
```

You do:

```
POST /users          (create)
GET /users           (list)
GET /users/123       (read)
PUT /users/123       (update)
DELETE /users/123    (delete)
```

**Why?** Consistency. Anyone who knows your API pattern can predict the endpoints.

## Resources vs Actions

### REST (Resource-Focused)

```
Resource: /users
Methods on resource:
  GET /users          - List all
  POST /users         - Create one
  GET /users/123      - Get specific
  PUT /users/123      - Update
  DELETE /users/123   - Delete
```

### Non-REST (Action-Focused)

```
Actions:
  POST /users/create      - Create
  POST /users/list        - List
  POST /users/get?id=123  - Get
  POST /users/update      - Update
  POST /users/delete      - Delete
```

The second is RPC (Remote Procedure Call) style. It works, but it's not REST and it's not as scalable.

**For backends**: REST APIs are the industry standard. Use them.

## Resource Naming (Critical)

### Nouns, Not Verbs

Wrong:
```
GET /getUsers
POST /createUser
DELETE /removeUser?id=123
```

Right:
```
GET /users
POST /users
DELETE /users/123
```

The verb (GET, POST, DELETE) describes the action. The resource (users) is the noun.

### Hierarchical Resources

Your resources often have relationships:

```
/users                           All users
/users/123                       User 123
/users/123/posts                 Posts by user 123
/users/123/posts/456             Specific post by user 123
/users/123/posts/456/comments    Comments on that post
/users/123/posts/456/comments/789  Specific comment
```

### Naming Conventions

Use **plural nouns** (most common):

```
/users          (all users)
/products       (all products)
/orders         (all orders)
/invoices       (all invoices)
```

Not:

```
/user           (singular - less common)
/product        (singular)
/order          (singular)
```

### Special Cases: Singular Resources

Sometimes you have singular resources (there's only one):

```
/profile         (logged-in user's profile, singular)
/settings        (app settings, singular)
/health          (health status, singular)

But still list/create collections:
/posts           (all posts)
/notifications   (all notifications)
```

## CRUD Operations with HTTP Methods

### Create (POST)

```python
# Request
POST /users HTTP/1.1
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}

# Response
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com"
}
```

Backend:

```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201
```

### Read (GET)

```python
# Request (list)
GET /users HTTP/1.1

# Response
HTTP/1.1 200 OK

[
  {"id": 1, "name": "Alice", "email": "alice@example.com"},
  {"id": 2, "name": "Bob", "email": "bob@example.com"}
]

# Request (specific)
GET /users/123 HTTP/1.1

# Response
HTTP/1.1 200 OK

{
  "id": 123,
  "name": "Alice",
  "email": "alice@example.com"
}
```

Backend:

```python
@app.route('/users', methods=['GET'])
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users])

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    return jsonify(user.to_dict())
```

### Update (PUT vs PATCH)

**PUT**: Replace entire resource

```python
# Request
PUT /users/123 HTTP/1.1

{
  "name": "Alice Updated",
  "email": "alice.new@example.com",
  "age": 30
}

# Your code replaces entire user with exactly this data
```

**PATCH**: Partial update

```python
# Request
PATCH /users/123 HTTP/1.1

{
  "email": "alice.new@example.com"
}

# Your code updates only the email, keeps other fields
```

Backend:

```python
# PUT: Replace
@app.route('/users/<int:user_id>', methods=['PUT'])
def replace_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    
    data = request.json
    # Delete old, create new (or just replace all fields)
    user.name = data.get('name', '')
    user.email = data.get('email', '')
    user.age = data.get('age')
    db.session.commit()
    return jsonify(user.to_dict())

# PATCH: Partial update
@app.route('/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    
    data = request.json
    # Only update fields provided
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    if 'age' in data:
        user.age = data['age']
    db.session.commit()
    return jsonify(user.to_dict())
```

### Delete (DELETE)

```python
# Request
DELETE /users/123 HTTP/1.1

# Response
HTTP/1.1 204 No Content

# (no body)
```

Backend:

```python
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    
    db.session.delete(user)
    db.session.commit()
    return '', 204
```

## Filtering, Sorting, Pagination

You can't always return all resources. Use query parameters.

### Filtering

```
GET /users?role=admin
GET /users?status=active
GET /users?created_after=2023-01-01
```

Backend:

```python
@app.route('/users', methods=['GET'])
def list_users():
    query = User.query
    
    # Filter by role if provided
    if request.args.get('role'):
        query = query.filter_by(role=request.args.get('role'))
    
    # Filter by status if provided
    if request.args.get('status'):
        query = query.filter_by(status=request.args.get('status'))
    
    users = query.all()
    return jsonify([u.to_dict() for u in users])
```

### Sorting

```
GET /users?sort=name
GET /users?sort=-created_at        (- means descending)
GET /users?sort=name&sort=-created_at  (multiple sorts)
```

Backend:

```python
@app.route('/users', methods=['GET'])
def list_users():
    query = User.query
    
    # Handle sorting
    sort_by = request.args.get('sort', 'id')
    if sort_by.startswith('-'):
        # Descending
        column = getattr(User, sort_by[1:])
        query = query.order_by(column.desc())
    else:
        # Ascending
        column = getattr(User, sort_by)
        query = query.order_by(column.asc())
    
    users = query.all()
    return jsonify([u.to_dict() for u in users])
```

### Pagination

```
GET /users?page=1&limit=10
```

Responses should include pagination info:

```json
{
  "data": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1000,
    "pages": 100
  }
}
```

Backend:

```python
@app.route('/users', methods=['GET'])
def list_users():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    query = User.query
    total = query.count()
    
    users = query.limit(limit).offset((page - 1) * limit).all()
    
    return jsonify({
        'data': [u.to_dict() for u in users],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    })
```

### Practical Filters

Real-world filtering patterns:

```
# E-commerce
GET /products?category=electronics&price_min=100&price_max=500&in_stock=true

# Blog
GET /posts?author_id=123&tag=python&published=true&created_after=2023-01-01

# SaaS
GET /invoices?customer_id=456&status=paid&from_date=2023-01-01&to_date=2023-12-31
```

## Versioning (Strategic)

### Why Version?

You need to change your API. Old clients still use the old version.

```
v1 of API: POST /users accepts {"name": "Alice"}
v2 of API: POST /users requires {"first_name": "Alice", "last_name": "Smith"}

Old client still sends old format
New client needs new format
Both must work
```

### URL Path Versioning

```
/api/v1/users       (old version)
/api/v2/users       (new version)
/api/v3/users       (newest)

Same backend, different routes
```

Backend:

```python
# v1 routes
@app.route('/api/v1/users', methods=['POST'])
def create_user_v1():
    data = request.json
    # old format: {"name": "Alice"}
    user = User(name=data['name'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'name': user.name}), 201

# v2 routes
@app.route('/api/v2/users', methods=['POST'])
def create_user_v2():
    data = request.json
    # new format: {"first_name": "Alice", "last_name": "Smith"}
    user = User(
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name
    }), 201
```

### Header Versioning

```
GET /users HTTP/1.1
Accept: application/vnd.example.v2+json

Your backend checks Accept header
Responds differently based on version
```

Less common, but cleaner.

### No Versioning (Advanced)

```
/users          (always latest)

Backwards compatible changes:
✓ Adding new optional field
✓ Adding new endpoint
✓ Deprecating old field (return empty/null)

Breaking changes:
✗ Removing field
✗ Changing response format
✗ Changing behavior
```

For backends, versioning via URL path is most common.

## Idempotency and Safety

### Safe Operations (Don't Change State)

```
GET /users      (safe, no side effects)
HEAD /users     (safe, check if resource exists)
OPTIONS /users  (safe, ask what's available)
```

Any safe operation can be called multiple times without consequence.

### Idempotent Operations (Same Result When Repeated)

```
PUT /users/123 {name: "Alice"}      (idempotent)
  First call: User 123 name becomes Alice
  Second call: User 123 name is still Alice
  Third call: Same

DELETE /users/123                    (idempotent)
  First call: Deletes user
  Second call: Already deleted, returns 404 (or 204)
  Third call: Same

GET /users/123                       (idempotent)
  Returns same data
```

Non-idempotent:

```
POST /users {name: "Alice"}          (not idempotent)
  First call: Creates user 1
  Second call: Creates user 2
  Third call: Creates user 3
```

### Why Idempotency Matters

Networks are unreliable. Requests might be retried:

```
Client sends: POST /orders {item: "laptop"}
Server processes (creates order 1000)
Response lost in network

Client retries: POST /orders {item: "laptop"}
Server processes (creates order 1001)

Result: Duplicate order!

---

Client sends: PUT /orders/1000 {status: "shipped"}
Server processes (order marked shipped)
Response lost in network

Client retries: PUT /orders/1000 {status: "shipped"}
Server processes (order already shipped, stays shipped)

Result: Idempotent, no problem!
```

### Handling Idempotency

For POST (inherently not idempotent):

```python
# Solution: Client provides unique ID
POST /orders HTTP/1.1
Idempotency-Key: req-12345-abc

{
  "item": "laptop",
  "quantity": 1
}

# Server implementation
@app.route('/orders', methods=['POST'])
def create_order():
    idempotency_key = request.headers.get('Idempotency-Key')
    
    # Check if we've seen this before
    existing = Order.query.filter_by(
        idempotency_key=idempotency_key
    ).first()
    
    if existing:
        # Return cached response
        return jsonify(existing.to_dict()), 201
    
    # New request, create order
    data = request.json
    order = Order(
        item=data['item'],
        quantity=data['quantity'],
        idempotency_key=idempotency_key
    )
    db.session.add(order)
    db.session.commit()
    return jsonify(order.to_dict()), 201
```

## Common REST Anti-Patterns

### Anti-Pattern 1: RPC Style

Wrong:
```
POST /users/create
POST /users/delete
POST /users/update
GET /users/list
```

Right:
```
POST /users
DELETE /users/123
PUT /users/123
GET /users
```

### Anti-Pattern 2: Verbs in URL

Wrong:
```
GET /users/get
POST /users/create
DELETE /users/delete
```

Right:
```
GET /users
POST /users
DELETE /users
```

### Anti-Pattern 3: Action-Based Endpoints

Wrong:
```
POST /users/send-email
POST /users/generate-report
POST /users/export-data
```

Right (if possible):
```
POST /users/123/email        (send email to user)
POST /notifications/reports  (create a report)
GET /exports?type=users      (get export data)
```

### Anti-Pattern 4: Inconsistent Response Format

Wrong:

```json
// GET /users/1
{"id": 1, "name": "Alice"}

// POST /users
{"user_id": 2, "user_name": "Bob"}

// GET /users/3
{"data": {"id": 3, "name": "Charlie"}}
```

Right:

```json
// All endpoints return same format
{"id": 1, "name": "Alice"}
{"id": 2, "name": "Bob"}
{"id": 3, "name": "Charlie"}
```

### Anti-Pattern 5: Leaking Internal Implementation

Wrong:
```
GET /users/by_database_id/123
GET /users/internal_id/456
GET /v1.2.3/users          (version in minor)
```

Right:
```
GET /v2/users/123
GET /users/123
```

## Backend Design: Complete Example

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/db'
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email}

# List users with filtering, sorting, pagination
@app.route('/api/v1/users', methods=['GET'])
def list_users():
    # Filtering
    query = User.query
    if request.args.get('name'):
        query = query.filter(User.name.contains(request.args.get('name')))
    
    # Sorting
    sort_by = request.args.get('sort', 'id')
    if sort_by.startswith('-'):
        query = query.order_by(getattr(User, sort_by[1:]).desc())
    else:
        query = query.order_by(getattr(User, sort_by))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    total = query.count()
    
    users = query.limit(limit).offset((page - 1) * limit).all()
    
    return jsonify({
        'data': [u.to_dict() for u in users],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    })

# Create user
@app.route('/api/v1/users', methods=['POST'])
def create_user():
    data = request.json
    
    if not data or not data.get('name') or not data.get('email'):
        return {'error': 'name and email required'}, 400
    
    if User.query.filter_by(email=data['email']).first():
        return {'error': 'email already exists'}, 409
    
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201

# Get single user
@app.route('/api/v1/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    return jsonify(user.to_dict())

# Update user
@app.route('/api/v1/users/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    
    data = request.json
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if User.query.filter_by(email=data['email']).first():
            return {'error': 'email already exists'}, 409
        user.email = data['email']
    
    db.session.commit()
    return jsonify(user.to_dict())

# Delete user
@app.route('/api/v1/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404
    
    db.session.delete(user)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## Production Notes

### 1. API Documentation

Clients need to know what endpoints exist. Use OpenAPI/Swagger:

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: Users API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      parameters:
        - name: page
          in: query
          type: integer
        - name: limit
          in: query
          type: integer
    post:
      summary: Create user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
```

### 2. Deprecation

Don't just remove API versions. Deprecate first:

```python
@app.route('/api/v1/users', methods=['GET'])
def list_users_v1():
    response = make_response(list_users_v2())
    response.headers['Deprecation'] = 'true'
    response.headers['Sunset'] = 'Sun, 01 Jan 2025 00:00:00 GMT'
    return response

@app.route('/api/v2/users', methods=['GET'])
def list_users_v2():
    # Current implementation
    pass
```

### 3. Rate Limiting

Prevent abuse:

```nginx
# In Nginx reverse proxy
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

location /api/ {
    limit_req zone=api burst=10;
    proxy_pass http://backend;
}
```

### 4. Error Responses

Consistent error format:

```python
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'error': 'bad_request',
        'message': 'Invalid request',
        'details': str(error)
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'not_found',
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'internal_server_error',
        'message': 'An error occurred'
    }), 500
```

---

## Module 3 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. Your API accepts both `/user/123` and `/users/123`. Is this RESTful?
   a) Yes, both work fine
   b) No, use consistent resource naming
   c) Yes, REST doesn't mandate plural
   d) No, never use path parameters

2. A PATCH request to `/users/123` should:
   a) Replace entire user with provided fields
   b) Update only the provided fields
   c) Return only the modified fields
   d) Always return 201 Created

3. You need to retrieve only active users, sorted by name, page 2, 20 per page. What's the URL?
   a) `GET /users/active/sorted/name/page/2/limit/20`
   b) `GET /users?status=active&sort=name&page=2&limit=20`
   c) `POST /users/filter` with body
   d) `GET /users/active` (custom endpoint)

4. Your API uses Idempotency-Key header. What should POST do if same key is sent twice?
   a) Always create a new resource
   b) Return the previously created resource
   c) Return error "duplicate request"
   d) Ignore the second request

5. You're deprecating API v1 in favor of v2. What's the right approach?
   a) Stop v1 immediately, clients must update
   b) Keep v1 working, add Deprecation header, set Sunset date
   c) Return 301 redirect from v1 to v2
   d) Keep both versions indefinitely

### Practical Networking Tasks

**Task 1: Design Complete REST API**

Design a REST API for a simple e-commerce system:
- Products (list, search, get details, create, update, delete)
- Orders (list user's orders, get order details, create, cancel)
- Customers (user profile, update profile)

For each resource, define:
- All endpoints with methods
- Query parameters (filtering, sorting, pagination)
- Request body format (for POST/PATCH/PUT)
- Response format
- Status codes returned

Document using curl commands:

```bash
# List products with filters
curl "http://localhost:5000/api/v1/products?category=electronics&price_min=100"

# Create order
curl -X POST http://localhost:5000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 123, "items": [...]}'
```

**Task 2: Build REST API with Versioning**

- Create Flask API with v1 and v2 versions
- v1: Simple user endpoint returning `{"id": 1, "name": "Alice"}`
- v2: Updated format returning `{"id": 1, "first_name": "Alice", "last_name": "Smith"}`
- Both versions accessible, no breaking changes
- Add deprecation headers to v1
- Test with curl to verify both work

### Production Incident Scenario

**Incident**: Clients report your API is creating duplicate records when making POST requests.

```
Client sends: POST /orders {"item": "laptop"}
Gets response: 500 Internal Server Error

Retries: POST /orders {"item": "laptop"}
Success: Creates order 1234

Then sees: Order created, but when they fetch orders, there are TWO orders with "laptop"
```

Questions:

1. What went wrong? (Why were two orders created?)
2. What should happen on retry in a well-designed API?
3. How would you prevent this in the future?
4. What HTTP header could the client use to help with this?
5. How would you implement idempotency handling in your code?

---

**Next**: [Module 4: WebSockets](04-websockets.md)
