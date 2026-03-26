# Revenue Intelligence Platform

Repositório de analytics de receita orientado a produção que transforma comportamento de clientes e pedidos em saídas batch governadas, tabelas para warehouse, artefatos executivos de decisão e um workspace Streamlit para ação comercial.

Versões disponíveis:

- [Internacional](README.md)
- [Português de Portugal](README.pt-PT.md)

## Resumo Executivo

Este repositório foi desenhado para responder às perguntas que um hiring manager, tech lead ou avaliador sênior costuma fazer sobre projetos de dados:

- existe um caminho oficial de execução?
- o pipeline é reprocessável com segurança?
- os outputs são governados e validados?
- há evidência operacional quando algo falha?
- o dashboard consome artefatos confiáveis em vez de reimplementar a lógica crítica?

Resposta curta: sim.

## Leitura Rápida Para Reviewer

Em menos de 30 segundos, alguém avaliando o repositório deve conseguir ver que ele tem:

- um caminho oficial de execução batch
- outputs governados com contratos e validação
- evidência operacional via manifests, snapshots e relatórios de qualidade
- consumo downstream por Streamlit, API, SQL e dbt
- CI que vai além de teste unitário e cobre smoke e build

## Por Que Este Repositório Existe

Muitos projetos de portfólio param em notebooks, scripts ad hoc ou um dashboard isolado. Este repositório é propositalmente mais operacional:

- um entrypoint batch oficial
- saídas determinísticas e reprocessáveis
- manifests, logs, snapshots e retenção de execução
- artefatos processados com validação e contratos
- consumidores downstream que leem o core batch em vez de substituí-lo

O objetivo não é simular uma plataforma enterprise sem substância. O objetivo é demonstrar critério de engenharia em um repositório pequeno o suficiente para ser auditado de ponta a ponta.

## Valor de Negócio

A plataforma converte comportamento de clientes em ativos que apoiam decisões comerciais e de retenção:

- risco de churn e propensão de próxima compra
- unit economics por canal de aquisição
- retenção por coorte
- recomendações por cliente com impacto simulado
- snapshots executivos de KPI e monitoramento
- tabelas de warehouse prontas para SQL e consumo estilo dbt

Para um avaliador técnico, o sinal prático é direto: este não é um showcase de notebook disfarçado de plataforma. É um sistema de dados pequeno, mas disciplinado, com ownership claro de runtime e responsabilidade sobre consumidores downstream.

## Caminho Oficial de Execução

```powershell
python -m src.pipeline run
```

O pipeline batch é a fonte oficial de verdade. O Streamlit, a API, o warehouse e o projeto dbt consomem as saídas produzidas por ele.

## Arquitetura

```mermaid
flowchart LR
    A[Entradas raw ou fonte sintética] --> B[Bronze]
    B --> C[Silver]
    C --> D[Features e scoring]
    D --> E[Analytics curado]
    E --> F[Reporting e monitoramento]
    D --> G[Warehouse]
    F --> H[Streamlit]
    F --> I[API e consumidores dbt]
    G --> I
```

Características principais:

- arquitetura batch-first com reprodutibilidade local
- política explícita de runtime para retry, retenção, freshness e thresholds de qualidade
- validação de artefatos processados antes da conclusão do pipeline
- warehouse SQLite por padrão, com caminhos compatíveis para serviços e dbt

## Estrutura do Repositório

```text
.
|- .github/                workflows de CI, templates e governança do repositório
|- app/                    camada de apresentação em Streamlit
|  |- ui/                  primitives reutilizáveis e estilos
|  |- views/               seções da página e composição do dashboard
|  |- dashboard_data.py    carregamento cacheado e filtros
|  |- dashboard_i18n.py    dicionários EN, PT-BR e PT-PT
|  |- dashboard_metrics.py helpers compartilhados de formatação e KPIs
|- src/                    pipeline batch, modelagem, reporting, warehouse e política operacional
|- contracts/              schemas governados versionados e shims de compatibilidade
|- services/               interfaces de serviço voltadas a runtime
|- api/                    shim de compatibilidade para imports da API
|- tests/                  cobertura comportamental, confiabilidade, contratos, API e warehouse
|- docs/                   arquitetura, onboarding, runbooks, ADRs e release notes
|- scripts/                smoke tests e automações operacionais leves
|- dbt/                    camada analítica downstream sobre os outputs do warehouse
|- orchestration/          exemplos de scheduler e wrappers de deploy
|- metrics/                definições de métricas semânticas consumidas pelo pipeline
|- sql/                    DDL do warehouse e assets SQL downstream
|- data/                   outputs locais de runtime, manifests, snapshots e warehouse
|- notebooks/              exploração isolada, fora do caminho oficial de execução
|- main.py                 wrapper mínimo de entrada Python
|- Dockerfile*             builds de container para Streamlit e API
|- CHANGELOG.md            histórico de evolução orientado a releases
```

Referências principais:

- [docs/README.md](docs/README.md)
- [docs/architecture.md](docs/architecture.md)
- [docs/governance_framework.md](docs/governance_framework.md)
- [docs/runtime_surfaces.md](docs/runtime_surfaces.md)
- [docs/environments.md](docs/environments.md)
- [docs/ci_cd.md](docs/ci_cd.md)
- [docs/repository_structure.md](docs/repository_structure.md)
- [docs/runbook.md](docs/runbook.md)
- [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
- [docs/release_process.md](docs/release_process.md)
- [docs/deprecation_policy.md](docs/deprecation_policy.md)
- [docs/merge_policy.md](docs/merge_policy.md)
- [docs/sql_examples.md](docs/sql_examples.md)
- [docs/incident_playbooks.md](docs/incident_playbooks.md)
- [docs/hiring_review.md](docs/hiring_review.md)

## Sinais de Maturidade em Engenharia de Dados

- execução idempotente e reprocessável
- retry configurável por estágio
- janela explícita de backfill na CLI e nos manifests
- relatórios de freshness, qualidade e validação de artefatos processados
- manifests, logs e snapshots para rastreabilidade
- persistência em warehouse com validação de consumo downstream
- payload parceiro gerado a partir de exports processados governados
- dashboard Streamlit com smoke test no CI

## Workspace Streamlit

O dashboard não é uma segunda fonte de verdade. Ele consome os artefatos processados e está organizado em:

- `app/ui` para primitives de layout e consistência visual
- `app/views` para seções de negócio e fluxo de leitura
- `app/dashboard_data.py` para acesso cacheado aos artefatos
- `app/dashboard_i18n.py` para `EN`, `PT-BR` e `PT-PT`

## Setup Local

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .[dev]
Copy-Item .env.example .env
```

Setup opcional do CLI `dbt` em ambiente isolado:

```powershell
python -m venv .dbt-venv
.dbt-venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install dbt-core dbt-sqlite
```

Variáveis de ambiente mais importantes:

- `RIP_DATA_DIR`
- `RIP_WAREHOUSE_TARGET`
- `RIP_RETRY_ATTEMPTS`
- `RIP_QUALITY_MAX_NULL_FRACTION`
- `RIP_BACKFILL_START_DATE`
- `RIP_BACKFILL_END_DATE`

## Comandos Principais

Pipeline:

```powershell
python -m src.pipeline run
```

Backfill:

```powershell
python -m src.pipeline run --start-date 2025-01-01 --end-date 2025-03-31
```

Streamlit:

```powershell
streamlit run app/streamlit_app.py
```

Fluxo com Make:

```powershell
make verify
make smoke-dashboard
make pipeline
```

## Validação e Automação

Comandos centrais:

```powershell
python -m ruff check .
python -m black --check .
python -m isort --check-only .
python -m mypy src services contracts main.py
python -m pytest -q --cov=src --cov=services --cov=contracts --cov-report=term-missing
python scripts/smoke_dashboard.py
python scripts/smoke_api.py
python scripts/smoke_downstream_sql.py
python scripts/smoke_processed_exports.py
python scripts/smoke_partner_payload.py
python scripts/smoke_dbt_sqlite.py
python -m build
```

Camadas de automação:

- `Makefile` para o fluxo local do desenvolvedor
- `.pre-commit-config.yaml` para gates rápidos antes do commit
- `.github/workflows/ci.yml` para lint, testes, smoke e build
- `.github/workflows/ci.yml` separa validação de qualidade, governança, dbt sobre SQLite e containers para facilitar diagnóstico
- `.github/workflows/ci.yml` também valida consumo dbt real sobre o warehouse SQLite gerado pelo pipeline
- os smokes downstream compartilham um helper comum de runtime temporário em `scripts/smoke_support.py`

Checkpoints de governança:

- mudanças de runtime devem preservar `python -m src.pipeline run` como caminho canônico
- exemplos SQL devem permanecer portáveis para o ambiente SQLite-first documentado, salvo quando o dialeto exigido estiver explícito
- README, runbook, release notes e CI devem evoluir juntos quando o comportamento operacional mudar

## Exemplos de Consumo SQL

Veja [docs/sql_examples.md](docs/sql_examples.md) para queries práticas de consumo do warehouse cobrindo economics por canal, ranking de recomendações, retenção por coorte e visão executiva por segmento.

## Decisões Técnicas e Trade-offs

- SQLite é o warehouse padrão porque reprodutibilidade local vale mais do que exigir infraestrutura externa.
- O projeto é batch-first por escolha. Ele demonstra analytics engineering disciplinado sem fingir ser uma plataforma completa de streaming.
- O Streamlit consome artefatos em vez de recalcular a lógica crítica, preservando um único caminho oficial de execução.
- Compat shims existem, mas os caminhos canônicos seguem explícitos e documentados.

## Ordem Recomendada de Leitura

Se o objetivo é avaliar profundidade técnica, leia nesta ordem:

1. este `README`
2. [docs/architecture.md](docs/architecture.md)
3. [docs/runtime_surfaces.md](docs/runtime_surfaces.md)
4. [docs/runbook.md](docs/runbook.md)
5. [docs/troubleshooting_matrix.md](docs/troubleshooting_matrix.md)
6. [docs/adr/README.md](docs/adr/README.md)
7. [docs/repository_structure.md](docs/repository_structure.md)
8. [docs/hiring_review.md](docs/hiring_review.md)

## O Que Este Repositório Não É

- não é uma coleção de notebooks
- não é um monorepo enterprise fictício
- não é uma demo de streaming
- não é um clone de plataforma de MLOps

É um sistema batch orientado a produção, dimensionado de forma honesta para um portfólio sênior forte.

## Roadmap

Próximos passos de maior impacto:

1. expandir contratos e validação dos artefatos processados
2. aprofundar validação downstream de warehouse e dbt
3. acumular mais release notes pequenas e coerentes
4. adicionar uma estratégia leve de regressão visual para o dashboard

## Contribuição

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para expectativas de workflow, convenção de commits, validação e boundaries do repositório.
