# Olist Executive Views

Consultas curadas para demo executiva, organizadas por tema.

Uso:

```powershell
python -m src.file_queries --file sql/olist/views/revenue_board.sql
```

Objetivo:

- entregar uma leitura executiva curta e direta
- reduzir a necessidade de compor queries ad hoc durante demos
- usar apenas os artefatos governados já produzidos pelo pipeline

Consultas:

- `revenue_board.sql`: resumo executivo de receita, ticket, retenção e concentração
- `retention_board.sql`: leitura de retenção, churn proxy e ação prioritária
- `operations_board.sql`: leitura de entrega, atraso e satisfação
- `seller_board.sql`: concentração, watchlist e seller líder
- `geography_board.sql`: liderança geográfica e oportunidade por estado
