import requests
from django.db import transaction
from time import sleep
from banco.models import LogCarga
from django.utils import timezone



class BaseSyncService:

    endpoint_url = None
    model_class = None
    lookup_field = "id"

    def fetch_data(self):

        url = self.endpoint_url
        params = {
            "itens": 100,
            "pagina": 1,
        }

        while url:

            # TODO: implementar retry e tratamento de conexão

            for tentativa in range(1,5):
                try:
                    response = requests.get(
                        url,
                        params=params,
                        timeout=30,
                    )

                    response.raise_for_status()
                    payload = response.json()
                except requests.RequestException as e:
                    if tentativa == 4:
                        raise
                    sleep(2 ** tentativa)

            for item in payload.get("dados", []):
                yield item

            # Procura o link da próxima página
            next_link = next(
                (
                    link["href"]
                    for link in payload.get("links", [])
                    if link.get("rel") == "next"
                ),
                None,
            )

            url = next_link

            # Os parâmetros já estão incorporados no link seguinte
            params = None

    def map_item(self, item):
        raise NotImplementedError(
            "A subclasse deve implementar map_item()."
        )

    def sync(self):

        criados = 0
        atualizados = 0

        log = LogCarga.objects.create(
            inicio=timezone.now(),
            endpoint=self.endpoint_url or self.__class__.__name__,
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

                with transaction.atomic():

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

        
