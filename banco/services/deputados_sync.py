from banco.models import Deputados
from .base_sync import BaseSyncService
from django.utils import timezone


class DeputadoSyncService(BaseSyncService):
    endpoint_url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
    model_class = Deputados
    lookup_field = "id"

    def map_item(self, item):

        external_id = item["id"]

        defaults = {
            "nome": item["nome"],
            "sigla_partido": item.get("siglaPartido"),
            "sigla_uf": item.get("siglaUf"),
            "id_legislatura": item.get("idLegislatura"),
            "data_carga": timezone.now(),
        }

        return external_id, defaults
