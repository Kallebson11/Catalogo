from banco.models import Partidos
from .base_sync import BaseSyncService
from django.utils import timezone


class PartidoSyncService(BaseSyncService):
    endpoint_url = "https://dadosabertos.camara.leg.br/api/v2/partidos"
    model_class = Partidos
    lookup_field = "id"

    def map_item(self, item):

        external_id = item["id"]

        defaults = {
            "sigla":        item.get("sigla"),
            "nome":         item.get("nome"),
            "data_carga":   timezone.now(),
        }

        return external_id, defaults
