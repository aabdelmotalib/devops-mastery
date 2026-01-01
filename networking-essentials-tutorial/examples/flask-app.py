"""
Flask Backend Application - Production Ready

This is a sample backend application demonstrating:
- REST API design principles
- Authentication with JWT
- Rate limiting
- Health checks
- Structured logging
- Database integration
- Proper error handling
"""

from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
import uuid
from datetime import datetime, timedelta
import os
import json

# ==================== Configuration ====================

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Get instance ID from environment
INSTANCE_ID = os.getenv('INSTANCE_ID', 'unknown')

# ==================== Logging Setup ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add request ID to all logs
class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(request, 'request_id', 'N/A')
        record.instance_id = INSTANCE_ID
        return True

logger.addFilter(RequestIdFilter())

# ==================== Initialize Extensions ====================

jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": ["*"]}})
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ==================== Middleware ====================

@app.before_request
def add_request_id():
    """Add unique request ID for tracing"""
    request.request_id = str(uuid.uuid4())
    request.start_time = datetime.now()
    
    logger.info(f"{request.method} {request.path}", extra={
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr,
        'request_id': request.request_id
    })

@app.after_request
def add_response_headers(response):
    """Add headers and log response"""
    duration = (datetime.now() - request.start_time).total_seconds()
    
    # Add response headers
    response.headers['X-Request-ID'] = request.request_id
    response.headers['X-Instance-ID'] = INSTANCE_ID
    response.headers['X-Response-Time'] = str(duration)
    
    logger.info(f"{request.method} {request.path} - {response.status_code}", extra={
        'status_code': response.status_code,
        'duration': duration,
        'request_id': request.request_id
    })
    
    return response

# ==================== Models (Simplified In-Memory for Demo) ====================

# In production, use SQLAlchemy with proper database
users_db = {}  # user_id -> {username, password_hash, email}
products_db = {}  # product_id -> {name, price, inventory}
orders_db = {}  # order_id -> {user_id, product_id, quantity, total, status}

next_product_id = 1
next_order_id = 1

# ==================== Authentication Routes ====================

@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Stricter limit on login
def login():
    """Login and receive JWT token"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username']
    password = data['password']
    
    # Find user
    user = None
    user_id = None
    for uid, u in users_db.items():
        if u['username'] == username:
            user = u
            user_id = uid
            break
    
    if not user:
        logger.warning(f"Login failed: user not found", extra={
            'username': username,
            'request_id': request.request_id
        })
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check password
    if not check_password_hash(user['password_hash'], password):
        logger.warning(f"Login failed: invalid password", extra={
            'username': username,
            'request_id': request.request_id
        })
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Create token
    access_token = create_access_token(
        identity=user_id,
        expires_delta=timedelta(hours=24)
    )
    
    logger.info(f"Login successful", extra={
        'username': username,
        'request_id': request.request_id
    })
    
    return jsonify({
        'access_token': access_token,
        'username': username
    }), 200

@app.route('/api/v1/auth/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    """Register new user"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    username = data['username']
    password = data['password']
    email = data.get('email', '')
    
    # Check if username exists
    for u in users_db.values():
        if u['username'] == username:
            return jsonify({'error': 'Username already exists'}), 409
    
    # Create user
    user_id = len(users_db) + 1
    users_db[user_id] = {
        'username': username,
        'password_hash': generate_password_hash(password),
        'email': email,
        'created_at': datetime.now().isoformat()
    }
    
    logger.info(f"User registered", extra={
        'username': username,
        'user_id': user_id,
        'request_id': request.request_id
    })
    
    return jsonify({'user_id': user_id, 'username': username}), 201

@app.route('/api/v1/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    
    if user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    user = users_db[user_id]
    return jsonify({
        'user_id': user_id,
        'username': user['username'],
        'email': user['email'],
        'created_at': user['created_at']
    }), 200

# ==================== Product Routes ====================

@app.route('/api/v1/products', methods=['GET'])
@limiter.limit("100 per minute")
def list_products():
    """List products with pagination and filtering"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Validate pagination
    if page < 1 or limit < 1 or limit > 100:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    
    # Get all products
    all_products = []
    for pid, product in products_db.items():
        all_products.append({
            'id': pid,
            **product
        })
    
    # Pagination
    total = len(all_products)
    start = (page - 1) * limit
    end = start + limit
    products = all_products[start:end]
    
    return jsonify({
        'data': products,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        }
    }), 200

@app.route('/api/v1/products/<int:product_id>', methods=['GET'])
@limiter.limit("100 per minute")
def get_product(product_id):
    """Get single product"""
    if product_id not in products_db:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify({
        'id': product_id,
        **products_db[product_id]
    }), 200

@app.route('/api/v1/products', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_product():
    """Create new product (requires authentication)"""
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or not data.get('name') or data.get('price') is None:
        return jsonify({'error': 'Missing name or price'}), 400
    
    global next_product_id
    product_id = next_product_id
    next_product_id += 1
    
    products_db[product_id] = {
        'name': data['name'],
        'price': float(data['price']),
        'inventory': data.get('inventory', 0),
        'created_by': user_id,
        'created_at': datetime.now().isoformat()
    }
    
    logger.info(f"Product created", extra={
        'product_id': product_id,
        'user_id': user_id,
        'request_id': request.request_id
    })
    
    return jsonify({
        'id': product_id,
        **products_db[product_id]
    }), 201

@app.route('/api/v1/products/<int:product_id>', methods=['PATCH'])
@jwt_required()
@limiter.limit("10 per minute")
def update_product(product_id):
    """Update product"""
    user_id = get_jwt_identity()
    
    if product_id not in products_db:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.json
    
    # Update only provided fields
    if 'name' in data:
        products_db[product_id]['name'] = data['name']
    if 'price' in data:
        products_db[product_id]['price'] = float(data['price'])
    if 'inventory' in data:
        products_db[product_id]['inventory'] = data['inventory']
    
    products_db[product_id]['updated_at'] = datetime.now().isoformat()
    
    logger.info(f"Product updated", extra={
        'product_id': product_id,
        'user_id': user_id,
        'request_id': request.request_id
    })
    
    return jsonify({
        'id': product_id,
        **products_db[product_id]
    }), 200

@app.route('/api/v1/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit("10 per minute")
def delete_product(product_id):
    """Delete product"""
    user_id = get_jwt_identity()
    
    if product_id not in products_db:
        return jsonify({'error': 'Product not found'}), 404
    
    del products_db[product_id]
    
    logger.info(f"Product deleted", extra={
        'product_id': product_id,
        'user_id': user_id,
        'request_id': request.request_id
    })
    
    return '', 204

# ==================== Order Routes ====================

@app.route('/api/v1/orders', methods=['POST'])
@jwt_required()
@limiter.limit("10 per minute")
def create_order():
    """Create new order"""
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or not data.get('product_id') or not data.get('quantity'):
        return jsonify({'error': 'Missing product_id or quantity'}), 400
    
    product_id = data['product_id']
    quantity = data['quantity']
    
    # Validate product exists and has inventory
    if product_id not in products_db:
        return jsonify({'error': 'Product not found'}), 404
    
    product = products_db[product_id]
    if product['inventory'] < quantity:
        return jsonify({'error': 'Insufficient inventory'}), 409
    
    # Create order
    global next_order_id
    order_id = next_order_id
    next_order_id += 1
    
    total = product['price'] * quantity
    
    orders_db[order_id] = {
        'user_id': user_id,
        'product_id': product_id,
        'quantity': quantity,
        'total': total,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    # Decrease inventory
    products_db[product_id]['inventory'] -= quantity
    
    logger.info(f"Order created", extra={
        'order_id': order_id,
        'user_id': user_id,
        'product_id': product_id,
        'request_id': request.request_id
    })
    
    return jsonify({
        'id': order_id,
        **orders_db[order_id]
    }), 201

@app.route('/api/v1/orders', methods=['GET'])
@jwt_required()
def list_orders():
    """List user's orders"""
    user_id = get_jwt_identity()
    
    user_orders = []
    for order_id, order in orders_db.items():
        if order['user_id'] == user_id:
            user_orders.append({
                'id': order_id,
                **order
            })
    
    return jsonify({'data': user_orders}), 200

# ==================== Health Check Routes ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # In production, check database, cache, etc.
        return jsonify({
            'status': 'healthy',
            'instance_id': INSTANCE_ID,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", extra={
            'request_id': request.request_id
        })
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@app.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness check for kubernetes/load balancer"""
    # In production, check if app is ready to serve traffic
    return jsonify({'status': 'ready'}), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    # In production, return actual metrics
    return 'Not implemented', 501

# ==================== Error Handlers ====================

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'bad_request', 'message': str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'unauthorized', 'message': 'Authentication required'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'forbidden', 'message': 'Access denied'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'not_found', 'message': 'Resource not found'}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': 'rate_limit_exceeded', 'message': 'Too many requests'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}", extra={
        'request_id': request.request_id
    })
    return jsonify({'error': 'internal_server_error', 'message': 'An error occurred'}), 500

# ==================== Initialize Sample Data ====================

def init_sample_data():
    """Initialize with sample data"""
    # Create sample users
    users_db[1] = {
        'username': 'alice',
        'password_hash': generate_password_hash('password123'),
        'email': 'alice@example.com',
        'created_at': datetime.now().isoformat()
    }
    users_db[2] = {
        'username': 'bob',
        'password_hash': generate_password_hash('password456'),
        'email': 'bob@example.com',
        'created_at': datetime.now().isoformat()
    }
    
    # Create sample products
    products_db[1] = {
        'name': 'Laptop',
        'price': 999.99,
        'inventory': 50,
        'created_at': datetime.now().isoformat()
    }
    products_db[2] = {
        'name': 'Mouse',
        'price': 29.99,
        'inventory': 200,
        'created_at': datetime.now().isoformat()
    }
    products_db[3] = {
        'name': 'Keyboard',
        'price': 79.99,
        'inventory': 150,
        'created_at': datetime.now().isoformat()
    }

# ==================== Main ====================

if __name__ == '__main__':
    init_sample_data()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}", extra={
        'instance_id': INSTANCE_ID
    })
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=debug
    )
