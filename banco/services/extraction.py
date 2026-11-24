import requests
import zipfile

from pathlib import Path
from io import BytesIO


def baixar_despesas(ano, caminho_destino):

    url = f"http://www.camara.leg.br/cotas/Ano-{ano}.json.zip"

    destino = Path(caminho_destino)

    print(f"Baixando arquivo de despesas de {ano}...")

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    with zipfile.ZipFile(BytesIO(response.content)) as arquivo_zip:

        arquivo_json = next(
            nome for nome in arquivo_zip.namelist()
            if nome.endswith(".json")
        )

        destino.parent.mkdir(parents=True, exist_ok=True)

        destino.write_bytes(arquivo_zip.read(arquivo_json))

    print(f"Arquivo salvo em: {destino}")

