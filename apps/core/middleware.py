class JWTHeaderMiddleware:
    """
    Copia cookie 'access_token' para header Authorization apenas para
    requests que NÃO sejam rotas públicas (register/login).
    """

    def __init__(self, get_response):
        self.get_response = get_response

        self.PUBLIC_PATHS = (
            "/api/users/register/",
            "/api/users/login/",
            "/api/users/painel/usuario/",
            "/api/users/painel/loja/",
        )

    def __call__(self, request):
        if not any(request.path.startswith(p) for p in self.PUBLIC_PATHS):
            token = request.COOKIES.get("access_token")
            if token:
                request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return self.get_response(request)