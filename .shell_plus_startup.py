# Arquivo de inicialização do shell_plus
# Este arquivo é executado automaticamente quando você inicia o shell_plus

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.db.models import Q, F, Count, Sum, Avg

# Mensagem de boas-vindas
print("=" * 70)
print("🚀 Django Shell Plus com IPython")
print("=" * 70)
print("\n✅ Todos os modelos já foram importados automaticamente:")
print("   - User, Category, Transaction, RecurringTemplate")
print("   - InstallmentPlan, Installment, CreditCard, CreditCardInvoice")
print("\n✅ Funções úteis importadas:")
print("   - datetime, date, timedelta")
print("   - Decimal")
print("   - Q, F, Count, Sum, Avg")
print("\n💡 Dicas:")
print("   - Use TAB para autocomplete")
print("   - Use %history para ver histórico")
print("   - Use %timeit para medir performance")
print("   - Use ? após qualquer objeto para ver documentação")
print("=" * 70)
print()

