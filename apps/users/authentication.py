
from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Autentica usando o cookie 'access_token'.
    Se o token for inválido/expirado, ignora 
    """
    def authenticate(self, request):
        token = request.COOKIES.get("access_token")
        if not token:
            return None

        try:
            validated = self.get_validated_token(token)
            user = self.get_user(validated)
            return (user, validated)
        except Exception:
            # Não quebra a request; apenas desconsidera o token
            return None