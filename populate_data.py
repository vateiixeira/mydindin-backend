"""
Script para popular dados financeiros de 2025 no sistema MyDinDin
Execute com: python populate_data.py
"""

import os
import django
from datetime import date
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from finances.models import Category, Transaction

User = get_user_model()

# Dados da planilha - valores mensais de janeiro a dezembro de 2025
DADOS_PLANILHA = {
    # Receitas (valores positivos na planilha)
    'VINI': {
        'tipo': 'income',
        'categoria': 'Salário',
        'valores': [11000.00, 11616.00, 11000.00, 11000.00, 11000.00, 11000.00, 11262.00, 11000.00, 11000.00, 11000.00, 11000.00, 11000.00]
    },
    'LARI': {
        'tipo': 'income',
        'categoria': 'Outras Receitas',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 600.00, 0.00, 900.00, 1490.00, 1087.00, -500.00, -500.00]
    },
    
    # Despesas (valores negativos na planilha - salvamos como positivo pois o modelo já controla isso)
    'INVESTIMENTO (pagbank)': {
        'tipo': 'expense',
        'categoria': 'Investimentos',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 2000.00, 0.00, 0.00]
    },
    'VIAGEM': {
        'tipo': 'expense',
        'categoria': 'Viagem e Turismo',
        'valores': [900.00, 900.00, 300.00, 0.00, 400.00, 400.00, 0.00, 300.00, 300.00, 500.00, 500.00, 500.00]
    },
    'IPVA CARRO': {
        'tipo': 'expense',
        'categoria': 'Veículos',
        'valores': [250.00, 250.00, 250.00, 250.00, 250.00, 250.00, 250.00, 250.00, 250.00, 700.00, 700.00, 700.00]
    },
    'SEGURO CARRO': {
        'tipo': 'expense',
        'categoria': 'Seguros',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
    },
    'CONSORCIO': {
        'tipo': 'expense',
        'categoria': 'Consórcio',
        'valores': [973.00, 984.00, 1388.00, 1007.00, 1019.00, 1031.00, 1043.00, 1055.00, 1068.00, 1080.00, 1093.00, 1106.00]
    },
    'CARRO HARLEY': {
        'tipo': 'expense',
        'categoria': 'Veículos',
        'valores': [1200.00, 2500.00, 2000.00, 2000.00, 2000.00, 2000.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
    },
    'FLOR': {
        'tipo': 'expense',
        'categoria': 'Presentes',
        'valores': [1000.00, 1000.00, 1000.00, 1000.00, 1000.00, 1300.00, 1000.00, 1050.00, 1000.00, 1000.00, 1000.00, 1000.00]
    },
    'CARTÃO NUBANK': {
        'tipo': 'expense',
        'categoria': 'Cartão de Crédito',
        'valores': [3105.00, 2703.00, 3308.00, 5606.00, 4475.00, 5257.00, 4583.00, 4713.74, 4567.00, 2446.00, 1000.00, 1000.00]
    },
    'GASOLINA': {
        'tipo': 'expense',
        'categoria': 'Combustível',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 200.00, 200.00, 200.00, 200.00, 200.00]
    },
    'CARTÃO ITAU': {
        'tipo': 'expense',
        'categoria': 'Cartão de Crédito',
        'valores': [155.00, 549.00, 994.00, 994.00, 994.00, 994.00, 994.00, 994.00, 874.00, 0.00, 0.00, 0.00]
    },
    'CASA': {
        'tipo': 'expense',
        'categoria': 'Moradia',
        'valores': [590.00, 590.00, 590.00, 590.00, 595.00, 595.00, 596.00, 596.00, 596.00, 600.00, 600.00, 600.00]
    },
    'INTERNET': {
        'tipo': 'expense',
        'categoria': 'Internet',
        'valores': [169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90, 169.90]
    },
    'PAIOL': {
        'tipo': 'expense',
        'categoria': 'Alimentação',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 240.00, 240.00, 240.00, 240.00, 240.00]
    },
    'LUZ': {
        'tipo': 'expense',
        'categoria': 'Energia Elétrica',
        'valores': [303.00, 253.00, 323.00, 334.00, 324.00, 284.00, 298.00, 315.00, 347.00, 370.00, 350.00, 350.00]
    },
    'ÁGUA': {
        'tipo': 'expense',
        'categoria': 'Água e Esgoto',
        'valores': [74.00, 77.00, 97.00, 78.00, 87.00, 87.00, 86.00, 78.00, 95.00, 95.00, 86.00, 86.00]
    },
    'FAXINA': {
        'tipo': 'expense',
        'categoria': 'Limpeza',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 200.00, 200.00, 200.00, 200.00]
    },
    'RESTAURANTE/ROLES': {
        'tipo': 'expense',
        'categoria': 'Lazer e Entretenimento',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]
    },
    'ACADEMIA': {
        'tipo': 'expense',
        'categoria': 'Saúde e Bem-estar',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 270.00, 0.00, 0.00]
    },
    'MARMITA': {
        'tipo': 'expense',
        'categoria': 'Alimentação',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 340.00, 340.00, 250.00, 250.00, 250.00]
    },
    'DAS MEI': {
        'tipo': 'expense',
        'categoria': 'Impostos',
        'valores': [75.60, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00, 81.00]
    },
    'OUTROS': {
        'tipo': 'expense',
        'categoria': 'Outras Despesas',
        'valores': [0.00, 0.00, 0.00, 0.00, 0.00, 120.00, 147.00, 147.00, 27.00, 27.00, 27.00, 27.00]
    },
}

# Meses de 2025
MESES = [
    date(2025, 1, 1),   # Janeiro
    date(2025, 2, 1),   # Fevereiro
    date(2025, 3, 1),   # Março
    date(2025, 4, 1),   # Abril
    date(2025, 5, 1),   # Maio
    date(2025, 6, 1),   # Junho
    date(2025, 7, 1),   # Julho
    date(2025, 8, 1),   # Agosto
    date(2025, 9, 1),   # Setembro
    date(2025, 10, 1),  # Outubro
    date(2025, 11, 1),  # Novembro
    date(2025, 12, 1),  # Dezembro
]


def criar_ou_obter_usuario():
    """Cria ou obtém o primeiro usuário do sistema"""
    input_email = input("Digite o email do usuário: ")
    user = User.objects.get(email=input_email)
    if not user:
        raise ValueError("Usuário não encontrado")
    return user


def criar_categorias(user):
    """Cria todas as categorias necessárias"""
    categorias_necessarias = {
        # Receitas
        'Salário': 'income',
        'Outras Receitas': 'income',
        
        # Despesas
        'Investimentos': 'expense',
        'Viagem e Turismo': 'expense',
        'Veículos': 'expense',
        'Seguros': 'expense',
        'Consórcio': 'expense',
        'Presentes': 'expense',
        'Cartão de Crédito': 'expense',
        'Combustível': 'expense',
        'Moradia': 'expense',
        'Internet': 'expense',
        'Alimentação': 'expense',
        'Energia Elétrica': 'expense',
        'Água e Esgoto': 'expense',
        'Limpeza': 'expense',
        'Lazer e Entretenimento': 'expense',
        'Saúde e Bem-estar': 'expense',
        'Impostos': 'expense',
        'Outras Despesas': 'expense',
    }
    
    categorias_criadas = {}
    for nome, tipo in categorias_necessarias.items():
        categoria, created = Category.objects.get_or_create(
            name=nome,
            type=tipo,
            user=user,
            defaults={'description': f'Categoria {nome}'}
        )
        if created:
            print(f"✓ Categoria criada: {nome} ({tipo})")
        else:
            print(f"  Categoria já existe: {nome}")
        categorias_criadas[nome] = categoria
    
    return categorias_criadas


def popular_transacoes(user, categorias):
    """Popula as transações baseadas nos dados da planilha"""
    total_criadas = 0
    total_puladas = 0
    
    print("\n" + "="*60)
    print("Populando transações...")
    print("="*60)
    
    for descricao, dados in DADOS_PLANILHA.items():
        tipo = dados['tipo']
        categoria = categorias[dados['categoria']]
        valores = dados['valores']
        
        print(f"\n{descricao} ({tipo}):")
        
        for i, mes in enumerate(MESES):
            valor = abs(Decimal(str(valores[i])))  # Converter para positivo
            
            # Pular se o valor for zero
            if valor == 0:
                continue
            
            # Verificar se já existe transação similar
            existe = Transaction.objects.filter(
                user=user,
                description=descricao,
                transaction_date=mes,
                amount=valor,
                type=tipo
            ).exists()
            
            if existe:
                print(f"  - {mes.strftime('%m/%Y')}: R$ {valor:.2f} (já existe)")
                total_puladas += 1
                continue
            
            # Criar transação
            transaction = Transaction.objects.create(
                user=user,
                category=categoria,
                type=tipo,
                description=descricao,
                amount=valor,
                transaction_date=mes,
                status='pending'
            )
            print(f"  ✓ {mes.strftime('%m/%Y')}: R$ {valor:.2f}")
            total_criadas += 1
    
    print("\n" + "="*60)
    print(f"Total de transações criadas: {total_criadas}")
    print(f"Total de transações puladas (já existem): {total_puladas}")
    print("="*60)


def main():
    """Função principal"""
    print("="*60)
    print("SCRIPT DE POPULAÇÃO DE DADOS - MyDinDin 2025")
    print("="*60)
    
    # 1. Criar ou obter usuário
    print("\n1. Verificando usuário...")
    user = criar_ou_obter_usuario()
    
    # 2. Criar categorias
    print("\n2. Criando categorias...")
    categorias = criar_categorias(user)
    
    # 3. Popular transações
    print("\n3. Populando transações...")
    popular_transacoes(user, categorias)
    
    print("\n" + "="*60)
    print("✓ SCRIPT CONCLUÍDO COM SUCESSO!")
    print("="*60)
    
    # Mostrar resumo
    total_transactions = Transaction.objects.filter(user=user).count()
    total_income = Transaction.objects.filter(user=user, type='income').count()
    total_expense = Transaction.objects.filter(user=user, type='expense').count()
    
    print(f"\nResumo final:")
    print(f"  - Total de transações no sistema: {total_transactions}")
    print(f"  - Receitas: {total_income}")
    print(f"  - Despesas: {total_expense}")


if __name__ == '__main__':
    main()

