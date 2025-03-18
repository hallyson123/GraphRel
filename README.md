# GraphRel: Ferramenta de Conversão de Grafos para Relacional

## Descrição

**GraphRel** é uma ferramenta desenvolvida para converter dados de bancos orientados a grafos para bancos de dados relacionais. Utilizando um esquema no formato **PG-Schema** como entrada, a ferramenta gera um script SQL e permite migrar dados automaticamente para o banco relacional.

---

## Funcionalidades

- **Conversão de Nodos**: Transforma nodos de grafos em tabelas relacionais.
- **Conversão de Relacionamentos e Cardinalidades**: Lida com cardinalidades (1:1, 1:N, N:1 e N:N).
- **Tratamento de Propriedades**: Propriedades dos nodos e relacionamentos com suporte a tipos variados e listas.
- **Tratamento de Hierarquias de Tipos**

---

## Requisitos

1. **Python**
2. **Neo4j** (com a biblioteca `neo4j` instalada)
3. **PostgreSQL** (com a biblioteca `psycopg2` instalada)
4. **Bibliotecas necessárias**:
   - `neo4j`
   - `psycopg2`
   - `pickle`

# Como usar

- Configurar o Neo4j
- Configurar o PostgreSQL
- Clonar o Repositório
- Configurar o Arquivo de Conexão
    - No arquivo `main.py`, ajuste as configurações de conexão `NEO4J_CONFIG` e `DATABASE_CONFIG`.
- Carregue o dicionário de dados extraído da ferramenta `GPFuse`.
   - Certifique-se de que o arquivo `nos_dump.pkl` está no diretório correto.
- Abra um terminal e vá até a pasta `GraphRel`.
   - Execute o comando: `python.exe .\main.py`

## Resultados
- **graph_to_rel.sql**: Script para criar o banco e suas tabelas
- **insert_nodes.sql**: Inserts para nodos.
- **insert_rel.sql**: Inserts para relacionamentos.
- **Completude**: Teste para verificar se todos os dados foram inseridos.
- **Corretude**: Teste para verificar se os dados inseridos estão corretos.
