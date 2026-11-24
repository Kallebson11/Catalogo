from tempfile import SpooledTemporaryFile
from zipfile import ZipFile

import requests
from django.conf import settings
from .r2_storage import obter_cliente_r2


def salvar_despesas_no_r2(url_origem, ano):
    cliente = obter_cliente_r2()
    chave = f"despesas/{ano}/despesas.json"

    # A Câmara publica as despesas dentro de um ZIP. Use um arquivo temporário
    # que permanece em memória até 8 MiB e é removido ao sair do bloco.
    with SpooledTemporaryFile(max_size=8 * 1024 * 1024, mode="w+b") as arquivo_zip:
        with requests.get(
            url_origem,
            stream=True,
            timeout=(15, 300),
        ) as resposta:
            resposta.raise_for_status()
            resposta.raw.decode_content = True
            for bloco in resposta.iter_content(chunk_size=1024 * 1024):
                if bloco:
                    arquivo_zip.write(bloco)

        arquivo_zip.seek(0)
        with ZipFile(arquivo_zip) as arquivo:
            nome_json = next(
                nome for nome in arquivo.namelist()
                if nome.lower().endswith(".json")
            )
            with arquivo.open(nome_json) as conteudo_json:
                # A chave é fixa por ano: remova o objeto anterior antes de
                # gravar a nova carga, evitando manter cópias como objetos
                # separados no bucket.
                cliente.delete_object(
                    Bucket=settings.R2_BUCKET,
                    Key=chave,
                )
                cliente.upload_fileobj(
                    conteudo_json,
                    settings.R2_BUCKET,
                    chave,
                    ExtraArgs={"ContentType": "application/json"},
                )

    return chave
