"""Configuração mínima para executar a suíte sem segredos ou serviços reais."""

import os


_TEST_SETTINGS = {
    "SECRET_KEY": "pytest-only-not-a-deploy-secret",
    "DEBUG": "False",
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:",
    "USER": "",
    "PASSWORD": "",
    "HOST": "",
    "PORT": "",
    "DRIVER": "",
    "R2_ACCOUNT_ID": "pytest-account",
    "R2_ACCESS_KEY_ID": "pytest-access-key",
    "R2_SECRET_ACCESS_KEY": "pytest-only-not-a-deploy-secret",
    "R2_BUCKET": "pytest-bucket",
}

for setting_name, setting_value in _TEST_SETTINGS.items():
    os.environ.setdefault(setting_name, setting_value)
