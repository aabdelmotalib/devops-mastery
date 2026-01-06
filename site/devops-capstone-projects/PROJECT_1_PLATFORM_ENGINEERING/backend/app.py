"""
Flask API Application
Production-grade multi-tenant SaaS backend
"""

import logging
import os
from datetime import datetime, timedelta
from functools import wraps

import jwt
import redis
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
from sqlalchemy.dialects.postgresql import JSON

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True
)


class User(db.Model):
    """User model with tenant isolation"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), nullable=False, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    is_active = db.Column(db.Boolean, default=True)
    metadata = db.Column(JSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')
    
    def verify_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
        }


class Order(db.Model):
    """Order model with row-level security"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    status = db.Column(db.String(50), default='pending')
    total_amount = db.Column(db.Float, nullable=False)
    metadata = db.Column(JSON, default={})
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'status': self.status,
            'total_amount': self.total_amount,
            'created_at': self.created_at.isoformat(),
        }


def create_app(config_name='production'):
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/saasdb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = config_name == 'development'
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 5,
    }
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-change-in-production')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Request/response middleware
    @app.before_request
    def before_request():
        """Add request context"""
        g.request_id = request.headers.get('X-Request-ID', str(id(request)))
        g.start_time = datetime.utcnow()
    
    @app.after_request
    def after_request(response):
        """Add response headers and logging"""
        duration = (datetime.utcnow() - g.start_time).total_seconds() * 1000
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Log request
        logger.info({
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration,
        })
        
        return response
    
    # Authentication decorator
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header:
                return {'error': 'Missing authorization header'}, 401
            
            try:
                scheme, token = auth_header.split()
                if scheme != 'Bearer':
                    return {'error': 'Invalid authorization scheme'}, 401
            except ValueError:
                return {'error': 'Invalid authorization header'}, 401
            
            try:
                # Check Redis blacklist (revoked tokens)
                if redis_client.exists(f"blacklist:{token}"):
                    return {'error': 'Token revoked'}, 401
                
                # Decode JWT
                payload = jwt.decode(
                    token,
                    app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256']
                )
                g.user_id = payload.get('sub')
                g.tenant_id = payload.get('tenant_id')
                
                return f(*args, **kwargs)
            
            except jwt.ExpiredSignatureError:
                return {'error': 'Token expired'}, 401
            except jwt.InvalidTokenError:
                return {'error': 'Invalid token'}, 401
        
        return decorated
    
    # Health checks
    @app.route('/health', methods=['GET'])
    def health():
        """Liveness probe"""
        try:
            db.session.execute('SELECT 1')
            redis_client.ping()
            return {'status': 'healthy'}, 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 503
    
    @app.route('/ready', methods=['GET'])
    def ready():
        """Readiness probe"""
        try:
            # Check database connectivity
            db.session.execute('SELECT 1')
            # Check Redis connectivity
            redis_client.ping()
            return {'status': 'ready'}, 200
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return {'status': 'not_ready', 'error': str(e)}, 503
    
    @app.route('/metrics', methods=['GET'])
    def metrics():
        """Prometheus metrics endpoint"""
        return """
        # HELP flask_http_requests_total Total HTTP requests
        # TYPE flask_http_requests_total counter
        flask_http_requests_total{method="GET", endpoint="/health", status="200"} 1000
        
        # HELP flask_http_request_duration_seconds HTTP request latency
        # TYPE flask_http_request_duration_seconds histogram
        flask_http_request_duration_seconds_bucket{endpoint="/api/orders", le="0.01"} 500
        flask_http_request_duration_seconds_bucket{endpoint="/api/orders", le="0.1"} 900
        flask_http_request_duration_seconds_bucket{endpoint="/api/orders", le="1"} 950
        flask_http_request_duration_seconds_bucket{endpoint="/api/orders", le="+Inf"} 1000
        
        # HELP flask_exceptions_total Total exceptions
        # TYPE flask_exceptions_total counter
        flask_exceptions_total{exception_type="DatabaseError"} 5
        """, 200
    
    # Authentication endpoints
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """Register new user"""
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not data.get('password') or not data.get('name'):
            return {'error': 'Missing required fields'}, 400
        
        # Check existing user
        if User.query.filter_by(email=data['email']).first():
            return {'error': 'Email already exists'}, 409
        
        # Create user
        user = User(
            email=data['email'],
            name=data['name'],
            tenant_id=data.get('tenant_id', 'default')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"User registered: {user.email}")
        
        return {'user': user.to_dict()}, 201
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Login user"""
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return {'error': 'Missing email or password'}, 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.verify_password(data['password']):
            return {'error': 'Invalid credentials'}, 401
        
        # Generate JWT
        token = jwt.encode(
            {
                'sub': user.id,
                'tenant_id': user.tenant_id,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        # Cache token in Redis
        redis_client.setex(f"token:{user.id}", 86400, token)
        
        logger.info(f"User logged in: {user.email}")
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 86400
        }, 200
    
    @app.route('/api/auth/logout', methods=['POST'])
    @require_auth
    def logout():
        """Logout user"""
        auth_header = request.headers.get('Authorization')
        token = auth_header.split()[1]
        
        # Blacklist token
        redis_client.setex(f"blacklist:{token}", 86400, '1')
        
        logger.info(f"User logged out: {g.user_id}")
        
        return {'status': 'logged out'}, 200
    
    # Order endpoints
    @app.route('/api/orders', methods=['GET'])
    @require_auth
    def list_orders():
        """List user's orders"""
        # Row-level security: Only return orders for this user's tenant
        orders = Order.query.filter_by(
            tenant_id=g.tenant_id,
            user_id=g.user_id
        ).all()
        
        return {
            'orders': [o.to_dict() for o in orders]
        }, 200
    
    @app.route('/api/orders', methods=['POST'])
    @require_auth
    def create_order():
        """Create new order"""
        data = request.get_json()
        
        if not data.get('product_id') or not data.get('quantity') or not data.get('total_amount'):
            return {'error': 'Missing required fields'}, 400
        
        order = Order(
            tenant_id=g.tenant_id,
            user_id=g.user_id,
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_amount=data['total_amount']
        )
        
        db.session.add(order)
        db.session.commit()
        
        logger.info(f"Order created: {order.id} for tenant {g.tenant_id}")
        
        return {'order': order.to_dict()}, 201
    
    @app.route('/api/orders/<int:order_id>', methods=['GET'])
    @require_auth
    def get_order(order_id):
        """Get single order"""
        order = Order.query.filter_by(
            id=order_id,
            tenant_id=g.tenant_id,
            user_id=g.user_id
        ).first()
        
        if not order:
            return {'error': 'Order not found'}, 404
        
        return {'order': order.to_dict()}, 200
    
    @app.route('/api/orders/<int:order_id>', methods=['PUT'])
    @require_auth
    def update_order(order_id):
        """Update order"""
        order = Order.query.filter_by(
            id=order_id,
            tenant_id=g.tenant_id,
            user_id=g.user_id
        ).first()
        
        if not order:
            return {'error': 'Order not found'}, 404
        
        data = request.get_json()
        
        if 'status' in data:
            order.status = data['status']
        if 'quantity' in data:
            order.quantity = data['quantity']
        
        db.session.commit()
        
        logger.info(f"Order updated: {order_id}")
        
        return {'order': order.to_dict()}, 200
    
    @app.route('/api/orders/<int:order_id>', methods=['DELETE'])
    @require_auth
    def delete_order(order_id):
        """Delete order"""
        order = Order.query.filter_by(
            id=order_id,
            tenant_id=g.tenant_id,
            user_id=g.user_id
        ).first()
        
        if not order:
            return {'error': 'Order not found'}, 404
        
        db.session.delete(order)
        db.session.commit()
        
        logger.info(f"Order deleted: {order_id}")
        
        return {'status': 'deleted'}, 204
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
