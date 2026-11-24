# Catálogo de dados da Câmara dos Deputados

Projeto em desenvolvimento para coletar dados abertos da Câmara dos Deputados, armazená-los em SQL Server e preparar artefatos para análises posteriores.

## Estado atual

O fluxo funcional implementado é a ingestão por meio de um comando Django:

1. Consulta deputados e partidos na API Dados Abertos da Câmara e sincroniza os resultados no SQL Server.
2. Baixa o arquivo anual compactado de despesas (`Ano-{ano}.json.zip`) publicado pela Câmara.
3. Extrai o JSON e o envia ao bucket Cloudflare R2, usando a chave `despesas/{ano}/despesas.json`.
4. Lê o JSON do R2 em fluxo e sincroniza as despesas no SQL Server por `id_documento`.
5. Registra o resultado das cargas na tabela `stage.log_carga`.

O arquivo é baixado e processado por temporários descartáveis. Eles podem usar o diretório temporário do sistema quando passam de 8 MiB e são removidos ao fim da etapa. No R2, o processo remove o objeto da chave anual antes de enviar a nova carga; mantenha o versionamento do bucket desativado se não quiser conservar versões antigas.

O repositório também contém um script SQL, uma transformação do Pentaho e diagramas de arquitetura e modelo dimensional. A implementação de um lakehouse Bronze/Silver/Gold no Databricks e uma API REST própria ainda não estão presentes no código versionado.

## Tecnologias

- Python e Django.
- SQL Server, com o backend `mssql-django`.
- Cloudflare R2 acessado pela API compatível com S3 (`boto3`).
- API pública Dados Abertos da Câmara dos Deputados.
- `ijson` para ler o JSON de despesas sem carregá-lo inteiro na memória.
- Pentaho Data Integration: há uma transformação versionada em `PDI/`.

O Django REST Framework está listado nas dependências, mas atualmente `config/urls.py` expõe apenas a interface administrativa; a ingestão é executada pelo management command.

## Estrutura do repositório

```text
.
├── banco/
│   ├── management/commands/carregar_camara.py
│   ├── migrations/              # Migrações do app banco
│   ├── services/                # Sincronização, extração e acesso ao R2
│   ├── models.py                # Deputados, partidos, despesas e log de carga
│   └── tests.py                 # Arquivo de testes ainda sem casos implementados
├── config/                      # Configurações e URLs do Django
├── diagramas/                   # Arquitetura e Star Schema (Draw.io)
├── PDI/                         # Transformação do Pentaho
├── sql/scripts/                 # DDL de referência para tabelas do SQL Server
├── manage.py
├── requirements.txt
└── README.md
```

## Pré-requisitos

- Python compatível com as versões listadas em `requirements.txt`.
- SQL Server acessível pela máquina que executará o Django.
- Driver ODBC para SQL Server compatível com o driver configurado em `settings.ini`.
- Conta Cloudflare com R2 habilitado, bucket criado e credenciais S3 com permissão de leitura e escrita de objetos nesse bucket.
- Git.

O script `sql/scripts/criacao_tabelas.sql` documenta as tabelas do schema `stage`. Para uma instalação nova, crie o banco de dados e o schema necessários antes de aplicar as migrações. Não execute o script de criação sobre tabelas que já existem.

## Configuração local

Crie e ative um ambiente virtual e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Na raiz do projeto, crie `settings.ini`. Esse arquivo é ignorado pelo Git; não versione nem compartilhe seus segredos.

```ini
[settings]
SECRET_KEY = substitua-pela-chave-local-do-django
DEBUG = False
ENGINE = mssql
NAME = nome-do-banco
USER = usuario-do-banco
PASSWORD = senha-do-banco
HOST = servidor-do-banco
PORT = 1433
DRIVER = ODBC Driver 17 for SQL Server
R2_ACCOUNT_ID = id-da-conta-cloudflare
R2_ACCESS_KEY_ID = access-key-do-r2
R2_SECRET_ACCESS_KEY = secret-access-key-do-r2
R2_BUCKET = nome-do-bucket
```

Use os nomes e valores correspondentes à sua instalação. `R2_ACCOUNT_ID` deve ser somente o ID da conta; `R2_BUCKET`, somente o nome do bucket. O `R2_SECRET_ACCESS_KEY` é secreto e não pode ser recuperado novamente pelo painel após a criação das credenciais.

## Banco de dados e migrações

Com `settings.ini` configurado e a conexão com SQL Server disponível:

```powershell
python manage.py migrate
python manage.py showmigrations banco
```

As tabelas usadas pela aplicação são `stage.deputados`, `stage.partidos`, `stage.despesas` e `stage.log_carga`. A chave primária de despesas é `id_documento`.

## Executar a carga

Informe o ano das despesas:

```powershell
python manage.py carregar_camara --ano 2026
```

Cada execução sincroniza deputados e partidos, baixa e atualiza o JSON anual no R2 e, em seguida, grava as despesas no SQL Server. Os registros são criados ou atualizados pelo identificador do documento, permitindo reexecutar a carga. Quando a origem não informa `valorGlosa`, o código usa zero; quando falta `idDocumento`, tenta construir um identificador inteiro a partir de `numero`.

O comando altera dados no SQL Server e no R2. Execute-o apenas com as configurações e o ano desejados. O resumo informa quantos registros de cada conjunto foram criados e atualizados; os detalhes da execução ficam em `stage.log_carga`.

## Artefatos analíticos

- `diagramas/StarSchemaCatalogo.drawio`: desenho do modelo dimensional proposto.
- `diagramas/ArquiteturaCatálogo`: artefato de arquitetura do projeto.
- `PDI/Transformação 1.ktr`: transformação versionada do Pentaho.
- `sql/scripts/criacao_tabelas.sql`: DDL das tabelas de staging.

Esses artefatos documentam etapas de análise e transformação; não representam, por si só, uma implantação completa de Bronze/Silver/Gold ou de um workspace Databricks.

## Verificações

Para validar a configuração Django sem executar a carga:

```powershell
python manage.py check
```

O arquivo `banco/tests.py` ainda não contém testes automatizados de ingestão. A carga real exige conexão com a API da Câmara, com o bucket R2 e com o SQL Server.

## Fonte de dados

- API Dados Abertos: <https://dadosabertos.camara.leg.br/api/v2>
- Arquivos anuais de despesas: <https://www.camara.leg.br/cotas/>

## Autor

**Kallebe Almeida** — [LinkedIn](https://linkedin.com/in/kallebson11)
