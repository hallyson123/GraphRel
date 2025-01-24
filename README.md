# GraphRel: Ferramenta de Conversão de Grafos para Relacional

## Descrição

**GraphRel** é uma ferramenta desenvolvida para converter dados de bancos orientados a grafos para bancos de dados relacionais. Utilizando um esquema no formato **PG-Schema** como entrada, a ferramenta gera um script SQL e permite migrar dados automaticamente para o banco relacional.

---

## Funcionalidades

- **Conversão de Nodos**: Transforma nodos de grafos em tabelas relacionais.
- **Conversão de Relacionamentos e Cardinalidades**: Lida com cardinalidades (1:1, 1:N, N:N).
- **Tratamento de Propriedades**: Gerencia propriedades dos nodos e relacionamentos com suporte a tipos variados e listas.
- **Tratamento de Hierarquias de Tipos**

---

## Requisitos

1. **Python 3.8 ou superior**
2. **Neo4j** (com a biblioteca `neo4j` instalada)
3. **PostgreSQL** (com a biblioteca `psycopg2` instalada)
4. **Bibliotecas Python necessárias**:
   - `neo4j`
   - `psycopg2`
   - `pickle`

# Como usar

## Passo 1: Configurar o Neo4j
Certifique-se de que o Neo4j está rodando.

## Passo 2: Configurar o PostgreSQL
Garanta que o PostgreSQL está ativo.

## Passo 3: Clonar o Repositório
Clone este repositório:

## Passo 4: Configurar o Arquivo de Conexão
No arquivo main.py, ajuste as configurações de conexão NEO4J_CONFIG e DATABASE_CONFIG:

## Passo 5: Executar a Ferramenta
Carregue o dicionário de dados do Neo4j:

Certifique-se de que o arquivo nos_dump.pkl (dicionário gerado com as informações do grafo) está no diretório correto. E então, execute o script principal.

## Resultados
- **graph_to_rel.sql**: Script para criar o banco e suas tabelas
- **insert_nodes.sql**: Inserções para nós.
- **insert_rel.sql**: Inserts para relacionamentos.
- **Completude**: Teste para verificar se todos os dados foram inseridos.
- **Corretude**: Teste para verificar se os dados inseridos estão corretos.