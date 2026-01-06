"""
Global error handlers
"""
from flask import jsonify, g
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    """Register all error handlers"""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all HTTP exceptions"""
        response = {
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }
        
        if hasattr(g, 'request_id'):
            response['request_id'] = g.request_id
        
        return jsonify(response), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all uncaught exceptions"""
        app.logger.error(f"Unhandled exception: {error}")
        app.logger.error(traceback.format_exc())
        
        # Don't expose internal errors in production
        if app.config['DEBUG']:
            response = {
                'error': 'Internal Server Error',
                'message': str(error),
                'traceback': traceback.format_exc()
            }
        else:
            response = {
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }
        
        if hasattr(g, 'request_id'):
            response['request_id'] = g.request_id
        
        return jsonify(response), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 errors"""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': str(error)
        }), 422
