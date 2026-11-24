from django.core.management.base import BaseCommand

from banco.services.deputados_sync import DeputadoSyncService
from banco.services.partidos_sync import PartidoSyncService
from banco.services.despesas_sync import DespesasSyncService
from banco.services.despesas_storage import salvar_despesas_no_r2

class Command(BaseCommand):

    help = "Sincroniza os dados da Câmara dos Deputados."

    def add_arguments(self, parser):

        parser.add_argument(
            "--ano",
            type=int,
            required=True,
            help="Ano de referência das despesas.",
        )

    def handle(self, *args, **options):

        ano = options["ano"]

        self.stdout.write("Iniciando sincronização...")

        # 1. Deputados
        criados, atualizados = DeputadoSyncService().sync()

        self.stdout.write(
            f"Deputados: {criados} criados | "
            f"{atualizados} atualizados"
        )

        # 2. Partidos
        criados, atualizados = PartidoSyncService().sync()

        self.stdout.write(
            f"Partidos: {criados} criados | "
            f"{atualizados} atualizados"
        )

        # 3. Despesas
        url_despesas = f"https://www.camara.leg.br/cotas/Ano-{ano}.json.zip"
        chave = salvar_despesas_no_r2(url_despesas, ano)
        self.stdout.write(f"Arquivo de despesas enviado ao R2: {chave}")

        criados, atualizados = DespesasSyncService(ano).sync()

        self.stdout.write(
        f"Despesas de {ano}: {criados} criadas | "
        f"{atualizados} atualizadas"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Sincronização finalizada."
            )
        )
