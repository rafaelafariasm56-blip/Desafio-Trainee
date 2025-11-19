class JWTHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.PUBLIC_PATHS = (
            "/api/users/register/",
            "/api/users/login/",
            "/swagger",
            "/redoc",
            "/api/schema",
        )

    def __call__(self, request):
        if not any(request.path.startswith(p) for p in self.PUBLIC_PATHS):
            token = request.COOKIES.get("access_token")
            if token and "HTTP_AUTHORIZATION" not in request.META:
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        
        return self.get_response(request)