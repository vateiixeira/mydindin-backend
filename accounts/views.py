from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from finances.serializers import UserSerializer, UserRegistrationSerializer, UserProfileUpdateSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint para registro de novos usuários.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Gerar tokens JWT
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Usuário registrado com sucesso'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint para login de usuários usando email.
    Retorna tokens JWT (access e refresh).
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Email e password são obrigatórios'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Autenticar usando email ao invés de username
    user = authenticate(request, email=email, password=password)
    
    if user is None:
        return Response(
            {'error': 'Credenciais inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Gerar tokens JWT
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        },
        'message': 'Login realizado com sucesso'
    })


@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET  — retorna informações do usuário logado.
    PATCH — atualiza first_name e/ou last_name do usuário logado.
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    Troca a senha do usuário autenticado.

    Body: { current_password, new_password, new_password_confirm, refresh (opcional) }

    Se `refresh` for fornecido, o token é invalidado via blacklist e um novo par de
    tokens é retornado. Caso contrário, a senha é alterada mas tokens existentes
    permanecem válidos até sua expiração natural.
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    new_password_confirm = request.data.get('new_password_confirm', '')
    refresh_token_str = request.data.get('refresh')

    errors = {}

    if not current_password:
        errors['current_password'] = 'Campo obrigatório.'
    elif not request.user.check_password(current_password):
        errors['current_password'] = 'Senha atual incorreta.'

    if not new_password:
        errors['new_password'] = 'Campo obrigatório.'
    else:
        if new_password != new_password_confirm:
            errors['new_password_confirm'] = 'As senhas não coincidem.'
        try:
            validate_password(new_password, request.user)
        except DjangoValidationError as exc:
            errors['new_password'] = list(exc.messages)

    if errors:
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    # Validar o refresh token ANTES de alterar a senha. Se o token for inválido,
    # a senha não é modificada e o 400 é semanticamente correto.
    if refresh_token_str:
        try:
            old_token = RefreshToken(refresh_token_str)
            old_token.blacklist()
        except Exception:
            return Response(
                {'refresh': 'Token inválido ou já invalidado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    request.user.set_password(new_password)
    request.user.save()

    response_data = {'message': 'Senha alterada com sucesso.'}

    if refresh_token_str:
        new_refresh = RefreshToken.for_user(request.user)
        response_data['tokens'] = {
            'refresh': str(new_refresh),
            'access': str(new_refresh.access_token),
        }

    return Response(response_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Endpoint para logout (blacklist do refresh token).
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token é obrigatório'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response({'message': 'Logout realizado com sucesso'})
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
