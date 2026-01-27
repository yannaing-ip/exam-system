# core/middleware.py

import logging

logger = logging.getLogger("django.server")

class RequestIPLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get("REMOTE_ADDR")
        logger.info(f"Request from IP: {ip} {request.method} {request.path}")
        return self.get_response(request)
        
        