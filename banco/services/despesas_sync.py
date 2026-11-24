import ijson
from tempfile import SpooledTemporaryFile
from banco.models import Despesas, LogCarga
from django.utils import timezone
from django.conf import settings
from .r2_storage import obter_cliente_r2


class DespesasSyncService:

    model_class = Despesas
    lookup_field = "id_documento"

    def __init__(self, ano):
        self.ano = ano

    def fetch_data(self):
        cliente = obter_cliente_r2()
        chave = f"despesas/{self.ano}/despesas.json"

        # Baixe o objeto antes de sincronizar para não manter a conexão do R2
        # aberta durante os milhares de gravações no SQL Server. O temporário
        # é descartado ao sair do bloco (e só passa de 8 MiB para disco).
        with SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as corpo:
            cliente.download_fileobj(
                settings.R2_BUCKET,
                chave,
                corpo,
            )
            corpo.seek(0)
            yield from ijson.items(corpo, "dados.item")

    def map_item(self, item):

        external_id = item.get("idDocumento")
        if external_id is None:
            # Seis registros da fonte de 2026 não têm idDocumento. O campo
            # numero (por exemplo, "2026/933698") é único nesse arquivo;
            # convertê-lo em 2026933698 mantém um PK inteiro e estável.
            numero = str(item.get("numero", "")).replace("/", "")
            if not numero.isdigit():
                raise ValueError(
                    "Despesa sem idDocumento e sem numero válido para identificá-la."
                )
            external_id = int(numero)

        defaults = {
            "id_deputado":              item.get("idDeputado"),
            "ano":                      item.get("ano"),
            "mes":                      item.get("mes"),
            "tipo_despesa":             item.get("descricao"),
            "nome_fornecedor":          item.get("fornecedor"),
            "cnpj_cpf_fornecedor":      item.get("cnpjCPF"),
            "valor_documento":          item.get("valorDocumento"),
            # A tabela stage.despesas exige valor_glosa; na fonte, a glosa
            # pode vir nula quando não houve valor glosado.
            "valor_glosa":              item.get("valorGlosa") or 0,
            "valor_liquido":            item.get("valorLiquido"),
            "data_carga":               timezone.now(),
        }

        return external_id, defaults

    def sync(self):

        criados = 0
        atualizados = 0

        log = LogCarga.objects.create(
            inicio=timezone.now(),
            endpoint=self.__class__.__name__,
            ano=self.ano,
            lidos=0,
            inseridos=0,
            atualizados=0,
            status="S",
            erro=None,
        )

        try:

            for item in self.fetch_data():

                external_id, defaults = self.map_item(item)

                _, created = self.model_class.objects.update_or_create(
                    **{self.lookup_field: external_id},
                    defaults=defaults,
                )

                if created:
                    criados += 1
                else:
                    atualizados += 1

                log.status = "S"
                log.erro = None
        except Exception as exc:
            log.status = "E"
            log.erro = str(exc)
            raise
        finally:
            log.fim = timezone.now()
            log.lidos = criados + atualizados
            log.inseridos = criados
            log.atualizados = atualizados
            log.save(update_fields=[
                "fim",
                "lidos",
                "inseridos",
                "atualizados",
                "status",
                "erro",
            ])

        return criados, atualizados
