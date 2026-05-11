from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Carrega as categorias padrão no banco de dados'
    
    def handle(self, *args, **options):
        self.stdout.write('Carregando categorias padrão...')
        
        try:
            call_command('loaddata', 'default_categories.json')
            self.stdout.write(
                self.style.SUCCESS('Categorias padrão carregadas com sucesso!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao carregar categorias: {str(e)}')
            )

