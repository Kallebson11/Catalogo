import json
from banco.models import Despesas, LogCarga
from django.utils import timezone


class DespesasSyncService:

    model_class = Despesas
    lookup_field = "id_documento"

    def __init__(self, ano):
        self.ano = ano

    def fetch_data(self):

        caminho = (
            f"C:/Users/KallebeDanielGuedesA/Documents/"
            f"Scripts/Python/Django/APIs/Ano-{self.ano}.json"
        )

        with open(caminho, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return dados.get("dados", [])

    def map_item(self, item):

        external_id = item["idDocumento"]

        defaults = {
            "id_deputado":              item.get("idDeputado"),
            "ano":                      item.get("ano"),
            "mes":                      item.get("mes"),
            "tipo_despesa":             item.get("descricao"),
            "nome_fornecedor":          item.get("fornecedor"),
            "cnpj_cpf_fornecedor":      item.get("cnpjCPF"),
            "valor_documento":          item.get("valorDocumento"),
            "valor_glosa":              item.get("valorGlosa"),
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
            ano=2026,
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
