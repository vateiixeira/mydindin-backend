from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticação customizado que permite login com email.
    """
    
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        """
        Autentica o usuário usando email ao invés de username.
        Também aceita username para compatibilidade.
        """
        try:
            # Tentar autenticar com email ou username
            user = User.objects.get(
                Q(email=email) | Q(email=username)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # Se houver múltiplos usuários, retorna o primeiro
            user = User.objects.filter(
                Q(email=email) | Q(email=username)
            ).first()
        
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Retorna o usuário pelo ID.
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

