import ast
import io
import json
import re
import subprocess
import zipfile
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from banco.services import base_sync, despesas_storage, despesas_sync
from banco.services.deputados_sync import DeputadoSyncService
from banco.services.despesas_sync import DespesasSyncService


class FakeLog:
    def __init__(self, fields):
        self.__dict__.update(fields)
        self.saved_fields = None

    def save(self, update_fields):
        self.saved_fields = update_fields


class FakeLogManager:
    def __init__(self):
        self.log = None

    def create(self, **fields):
        self.log = FakeLog(fields)
        return self.log


class FakeObjectManager:
    def __init__(self, created_results):
        self.created_results = iter(created_results)
        self.calls = []

    def update_or_create(self, **kwargs):
        self.calls.append(kwargs)
        return object(), next(self.created_results)


def attach_fake_log(monkeypatch, module):
    manager = FakeLogManager()
    monkeypatch.setattr(module, "LogCarga", SimpleNamespace(objects=manager))
    return manager


def make_response(payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


def test_api_is_requested_and_extracts_nonempty_paginated_data(monkeypatch):
    service = DeputadoSyncService()
    service.endpoint_url = "https://api.test/deputados"
    first_page = make_response({
        "dados": [{"id": 1}, {"id": 2}],
        "links": [{"rel": "next", "href": "https://api.test/page/2"}],
    })
    second_page = make_response({"dados": [{"id": 3}], "links": []})
    get = Mock(side_effect=[first_page, second_page])
    monkeypatch.setattr(base_sync.requests, "get", get)

    rows = list(service.fetch_data())

    assert [row["id"] for row in rows] == [1, 2, 3]
    assert get.call_count == 2
    assert get.call_args_list[0].kwargs["timeout"] == 30
    assert get.call_args_list[1].args[0] == "https://api.test/page/2"


def test_api_rows_are_upserted_and_success_is_logged(monkeypatch):
    rows = [
        {"id": 1, "nome": "Deputado 1", "siglaPartido": "AA", "siglaUf": "SP", "idLegislatura": 57},
        {"id": 2, "nome": "Deputado 2", "siglaPartido": "BB", "siglaUf": "RJ", "idLegislatura": 57},
        {"id": 3, "nome": "Deputado 3", "siglaPartido": "CC", "siglaUf": "MG", "idLegislatura": 57},
    ]
    get = Mock(return_value=make_response({"dados": rows, "links": []}))
    monkeypatch.setattr(base_sync.requests, "get", get)
    monkeypatch.setattr(base_sync.transaction, "atomic", nullcontext)
    log_manager = attach_fake_log(monkeypatch, base_sync)
    manager = FakeObjectManager([True, False, True])
    service = DeputadoSyncService()
    service.model_class = SimpleNamespace(objects=manager)

    created, updated = service.sync()

    assert (created, updated) == (2, 1)
    assert len(manager.calls) == len(rows)
    assert all(call["id"] == row["id"] for call, row in zip(manager.calls, rows))
    assert log_manager.log.status == "S"
    assert log_manager.log.lidos == 3
    assert log_manager.log.inseridos == 2
    assert log_manager.log.atualizados == 1
    assert log_manager.log.fim is not None


def make_zip_with_json(payload):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr("Ano-2026.json", json.dumps(payload))
    return archive.getvalue()


def test_expense_archive_is_downloaded_validated_and_uploaded_to_r2(monkeypatch):
    payload = {"dados": [{"idDocumento": 901, "valorGlosa": "0.00"}]}
    archive_bytes = make_zip_with_json(payload)

    class FakeHttpResponse:
        raw = SimpleNamespace(decode_content=False)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            assert chunk_size > 0
            yield archive_bytes

    http_get = Mock(return_value=FakeHttpResponse())
    monkeypatch.setattr(despesas_storage.requests, "get", http_get)

    class FakeR2Client:
        def __init__(self):
            self.deleted = []
            self.upload = None

        def delete_object(self, **kwargs):
            self.deleted.append(kwargs)

        def upload_fileobj(self, fileobj, bucket, key, **kwargs):
            self.upload = (fileobj.read(), bucket, key, kwargs["ExtraArgs"])

    client = FakeR2Client()
    monkeypatch.setattr(despesas_storage, "obter_cliente_r2", lambda: client)
    monkeypatch.setattr(despesas_storage.settings, "R2_BUCKET", "test-bucket")

    key = despesas_storage.salvar_despesas_no_r2("https://camara.test/Ano-2026.json.zip", 2026)

    http_get.assert_called_once_with(
        "https://camara.test/Ano-2026.json.zip",
        stream=True,
        timeout=(15, 300),
    )
    assert key == "despesas/2026/despesas.json"
    assert client.deleted == [{"Bucket": "test-bucket", "Key": key}]
    uploaded_bytes, bucket, uploaded_key, extra_args = client.upload
    uploaded_json = json.loads(uploaded_bytes)
    assert uploaded_json["dados"]
    assert bucket == "test-bucket"
    assert uploaded_key == key
    assert extra_args["ContentType"] == "application/json"


def test_expenses_are_read_from_r2_and_all_rows_are_upserted_and_logged(monkeypatch):
    rows = [
        {"idDocumento": 51, "ano": 2026, "mes": 1, "valorGlosa": None},
        {"numero": "2026/900052", "ano": 2026, "mes": 1},
    ]
    json_bytes = json.dumps({"dados": rows}).encode()

    class FakeR2Client:
        def download_fileobj(self, bucket, key, fileobj):
            assert bucket == "test-bucket"
            assert key == "despesas/2026/despesas.json"
            fileobj.write(json_bytes)

    monkeypatch.setattr(despesas_sync, "obter_cliente_r2", FakeR2Client)
    monkeypatch.setattr(despesas_sync.settings, "R2_BUCKET", "test-bucket")
    service = DespesasSyncService(2026)
    extracted_rows = list(service.fetch_data())
    assert extracted_rows == rows

    log_manager = attach_fake_log(monkeypatch, despesas_sync)
    manager = FakeObjectManager([True, True])
    service.model_class = SimpleNamespace(objects=manager)
    created, updated = service.sync()

    assert (created, updated) == (2, 0)
    assert len(manager.calls) == len(rows)
    assert manager.calls[0]["id_documento"] == 51
    assert manager.calls[0]["defaults"]["valor_glosa"] == 0
    assert manager.calls[1]["id_documento"] == 2026900052
    assert log_manager.log.ano == 2026
    assert log_manager.log.status == "S"
    assert log_manager.log.lidos == 2
    assert log_manager.log.inseridos == 2
    assert log_manager.log.erro is None


def test_failed_expense_sync_is_logged_and_reraised(monkeypatch):
    log_manager = attach_fake_log(monkeypatch, despesas_sync)
    service = DespesasSyncService(2026)
    service.fetch_data = lambda: (_ for _ in ()).throw(RuntimeError("falha simulada"))

    with pytest.raises(RuntimeError, match="falha simulada"):
        service.sync()

    assert log_manager.log.status == "E"
    assert log_manager.log.erro == "falha simulada"
    assert log_manager.log.fim is not None


def test_tracked_files_do_not_include_local_secrets():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    tracked_paths = [Path(path.decode()) for path in result.stdout.split(b"\0") if path]
    secret_files = [
        path.as_posix()
        for path in tracked_paths
        if path.name.lower() == ".env" or path.suffix.lower() == ".ini"
    ]
    assert secret_files == []


def test_python_sources_are_syntactically_valid_and_use_required_naming():
    root = Path(__file__).resolve().parents[1]
    source_paths = [
        *root.glob("*.py"),
        *root.glob("banco/**/*.py"),
        *root.glob("config/**/*.py"),
        *root.glob("tests/**/*.py"),
    ]
    snake_case = re.compile(r"^_*[a-z][a-z0-9_]*$")
    constant_case = re.compile(r"^_*[A-Z][A-Z0-9_]*$")
    pascal_case = re.compile(r"^[A-Z][A-Za-z0-9]*$")
    violations = []

    for source_path in source_paths:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not snake_case.fullmatch(node.name) and not node.name.startswith("__"):
                    violations.append(f"{source_path}: função {node.name}")
                for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                    if argument.arg not in {"self", "cls"} and not snake_case.fullmatch(argument.arg):
                        violations.append(f"{source_path}: argumento {argument.arg}")
            elif isinstance(node, ast.ClassDef) and not pascal_case.fullmatch(node.name):
                violations.append(f"{source_path}: classe {node.name}")
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                if node.id != "_" and not (
                    snake_case.fullmatch(node.id) or constant_case.fullmatch(node.id)
                ):
                    violations.append(f"{source_path}: variável {node.id}")

    assert violations == []
