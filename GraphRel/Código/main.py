import psycopg2
from psycopg2 import sql
from neo4j import GraphDatabase
from GraphRel import gerar_script_sql
import pickle
import re

ARRAY_LIST = True
DUAS_TABELAS_CASO_DOIS = False
LISTA_COMO_TABELA = True

BATCH_SIZE = 1  # Tamanho dos lotes para inserção
MAX_LINES = 172000 # Quantidade maxima de linhas

name_db = "testerel" # nome do banco

# Configurações do postgres
DATABASE_CONFIG = {
    "user": "postgres",
    "password": "1F16EBD3",
    "host": "localhost",
    "port": 5432
}

def conectar_postgres(config):
    try:
        conn = psycopg2.connect(**config)
        print("Conexão com o PostgreSQL estabelecida com sucesso!")
        return conn
    
    except Exception as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        raise

def criar_banco(conn, db_name, script_sql):
    try:
        #autocommit para criar o banco fora de uma transação
        conn.autocommit = True
        with conn.cursor() as cur:
            # Criar o banco de dados
            cur.execute(f"CREATE DATABASE {db_name};")
            print(f"Banco de dados {db_name} criado com sucesso!")

        # Conectar ao novo banco de dados
        db_config = {key: value for key, value in DATABASE_CONFIG.items() if key != "dbname"}
        new_conn = psycopg2.connect(dbname=db_name, **DATABASE_CONFIG)
        
        with new_conn.cursor() as cur:
            cur.execute(script_sql)
            new_conn.commit()
            print(f"Script SQL executado com sucesso no banco {db_name}!")
        return new_conn

    except psycopg2.errors.DuplicateDatabase:
        print(f"O banco de dados {db_name} já existe.")
    except Exception as e:
        print(f"Erro ao criar o banco de dados ou executar o script: {e}")
        raise
    finally:
        # Restaurar o comportamento padrão de autocommit
        conn.autocommit = False

def inserir_em_lotes(conn, inserts, batch_size, file, max_lines=None, db_name=None, database_config=None):
    try:
        # Conectar ao banco correto se necessário
        if db_name and database_config:
            conn.close()
            conn = psycopg2.connect(dbname=db_name, **database_config)

        # Filtrar consultas vazias ou inválidas
        inserts = [query.strip() for query in inserts if query.strip()]

        total_processed = 0
        error_log_file = file

        with open(error_log_file, "w", encoding="utf-8") as error_log, conn.cursor() as cur:
            count_error = 0
            count_errors_resolved = 0
            c = 0

            for i in range(0, len(inserts), batch_size):
                lote = inserts[i:i + batch_size]

                # Se houver limite de linhas, ajustar o lote
                if max_lines is not None and total_processed + len(lote) > max_lines:
                    lote = lote[:max_lines - total_processed]

                for line_number, query in enumerate(lote, start=i + 1):
                    try:
                        cur.execute(query)
                    
                    except psycopg2.IntegrityError as e:
                        error_msg = str(e)
                        error_log.write(f"--------------------------------------------\n")
                        error_log.write(f"Linha {line_number}. {e}")
                        error_log.write(f"Query: {query}.\n")

                        # Tenta extrair o nome da coluna com regex
                        match = re.search(r'o valor nulo na coluna "(.*?)"', error_msg)

                        # Desbloquear a transação
                        conn.rollback()

                        if match:
                            col_name = match.group(1)
                            # Tenta extrair o nome da tabela a partir do comando INSERT
                            table_match = re.search(r'INSERT INTO\s+([^\s(]+)', query, re.IGNORECASE)
                            if table_match:
                                table_name = table_match.group(1)
                                #print(count_error, col_name, table_name)
                                try:
                                    # Remover a restrição de chave primaria
                                    query_key = f"""
                                                SELECT conname AS constraint_name, 
                                                    conrelid::regclass AS table_name, 
                                                    a.attname AS column_name
                                                FROM pg_constraint c
                                                JOIN pg_attribute a 
                                                    ON a.attnum = ANY(c.conkey) 
                                                    AND a.attrelid = c.conrelid
                                                WHERE c.contype = 'p'
                                                AND c.conrelid = '{table_name}'::regclass;
                                            """
                                    cur.execute(query_key)
                                    primary_keys = cur.fetchall()  # Obtém as chaves primárias
                                    pk_n = [pk[0] for pk in primary_keys]

                                    # if pk_n[0] == f"{table_name}_pkey":
                                    #     print("UNICA")
                                    #     pk_name = pk_n[0]
                                    #     c_name = [pk[2] for pk in primary_keys]
                                    #     column_name = c_name[0]
                                    #     table_name = f"{table_name}_pkey"
                                    #     # print(pk_name, column_name, table_name)
                                    
                                    if len(pk_n) > 1:
                                        # print("COMPOSTA")
                                        # print(primary_keys)
                                        pk_name = pk_n[0]
                                        c_name = [pk[2] for pk in primary_keys]
                                        column_name_1 = c_name[0]
                                        column_name_2 = c_name[1]
                                        column_name = f'{column_name_1, column_name_2}'
                                        # print(f"Constraint: {pk_name}, Tabela: {table_name}, Coluna: ({column_name})")

                                    else:
                                        print("UNICA")
                                        pk_name = pk_n[0]
                                        c_name = [pk[2] for pk in primary_keys]
                                        column_name = c_name[0]
                                        print(pk_name, column_name, table_name)

                                    primary_key = f'ALTER TABLE {table_name} DROP CONSTRAINT {pk_name}'
                                    cur.execute(primary_key)
                                    error_log.write(f"Chave primaria removida: {primary_key}\n")

                                    # Remover a restrição NOT NULL da coluna problemática
                                    # alter_drop = f'ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;'
                                    # cur.execute(alter_drop)
                                    # conn.commit()
                                    # error_log.write(f"Restrição NOT NULL removida: {alter_drop}\n")

                                    # Consulta para obter os nomes das colunas que atualmente são NOT NULL.
                                    select_cols = f"""
                                        SELECT column_name 
                                        FROM information_schema.columns
                                        WHERE table_schema = 'public'
                                        AND table_name = '{table_name}'
                                        AND is_nullable = 'NO';
                                    """
                                    cur.execute(select_cols)
                                    cols = cur.fetchall()
                                    not_null_columns = [c[0] for c in cols]
                                    error_log.write(f"Colunas com NOT NULL em {table_name}: {not_null_columns}\n")

                                    # print(table_name, cols)

                                    # Remove todas as restrições NOT NULL
                                    for col in not_null_columns:
                                        alter_drop = f'ALTER TABLE {table_name} ALTER COLUMN {col} DROP NOT NULL;'
                                        cur.execute(alter_drop)
                                        error_log.write(f"Comando executado: {alter_drop}\n")
                                    conn.commit()

                                    # Tentar reexecutar a query original
                                    cur.execute(query)
                                    conn.commit()
                                    error_log.write(f"Query reexecutada com sucesso na linha {line_number}.\n")
                                    error_log.write(f"Query: {query}\n")

                                    # # Remove registros com NULL antes de restaurar NOT NULL
                                    # delete_nulls = f'DELETE FROM {table_name} WHERE {col_name} IS NULL;'
                                    # cur.execute(delete_nulls)
                                    # conn.commit()
                                    # error_log.write(f"Remover resgistro com valor NULL: {delete_nulls}\n")

                                    # Remove registros com NULL antes de restaurar NOT NULL
                                    for col in not_null_columns:
                                        delete_nulls = f'DELETE FROM {table_name} WHERE {col} IS NULL;'
                                        cur.execute(delete_nulls)
                                        error_log.write(f"Remover resgistro com valor NULL: {delete_nulls}\n")
                                    conn.commit()

                                    # # Restaurar a restrição NOT NULL
                                    # alter_set = f'ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;'
                                    # cur.execute(alter_set)
                                    # conn.commit()
                                    # error_log.write(f"Restrição NOT NULL restaurada: {alter_set}\n")

                                    # Restaurar o NOT NULL em cada coluna
                                    for col in not_null_columns:
                                        alter_set = f'ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL;'
                                        cur.execute(alter_set)
                                        error_log.write(f"Restrição NOT NULL restaurada: {alter_set}\n")
                                    conn.commit()

                                    # Restaurar pk
                                    add_pk = f'ALTER TABLE {table_name} ADD CONSTRAINT {pk_name} PRIMARY KEY ({column_name_1}, {column_name_2});'
                                    cur.execute(add_pk)
                                    conn.commit()
                                    error_log.write(f"Chave primária restaurada: {add_pk}\n")

                                    count_errors_resolved += 1

                                except Exception as e2:
                                    conn.rollback()
                                    error_log.write(f"Erro na reexecução na linha {line_number} para coluna {col_name}: {e2}\n")
                                    error_log.write(f"Query com erro: {query}\n\n")
                                    count_error += 1
                                    continue

                            else:
                                error_log.write(f"Não foi possível extrair o nome da tabela na linha {line_number}.\n")
                                error_log.write(f"Query com erro: {query}\n\n")
                                count_error += 1
                                continue
                        else:
                            error_log.write(f"Não foi possível extrair o nome da coluna na linha {line_number}.\n")
                            error_log.write(f"Query com erro: {query}\n\n")
                            count_error += 1
                            continue

                conn.commit()
                total_processed += len(lote)
                # print(f"Lote {i // batch_size + 1} inserido com sucesso! Total processado: {total_processed}")

                # Interromper se atingir o limite de linhas
                if max_lines is not None and total_processed >= max_lines:
                    print(f"Limite de {max_lines} linhas atingido. Processamento finalizado.")
                    break

            error_log.write(f"--------------------------------------------\n")
            error_log.write(f"\nQuantidade de erros sem solução: {count_error}\n")
            error_log.write(f"Quantidade de erros solucionados: {count_errors_resolved}\n")
            print(f"Erros registrados em {file}.")

    except Exception as e:
        conn.rollback()
        with open("erros_insercao_criticos.txt", "w", encoding="utf-8") as critical_log:
            critical_log.write(f"Erro crítico: {e}\n")
        raise

def verificar_completude(conn_postgres, conn_neo4j):
    try:
        resultados_completude = {"neo4j": {}, "postgres": {}}

        # Obter contagens específicas no Neo4j
        with conn_neo4j.session() as session:
            nodos_neo4j = session.run("""
                MATCH (n)
                WITH labels(n) AS tipos, count(n) AS total
                RETURN tipos, total
            """).values()

            rels_neo4j = session.run("""
                MATCH ()-[r]->()
                WITH type(r) AS tipo, count(r) AS total
                RETURN tipo, total
            """).values()

            resultados_completude["neo4j"]["nodes"] = {tuple(labels): total for labels, total in nodos_neo4j}
            resultados_completude["neo4j"]["relationships"] = {tipo: total for tipo, total in rels_neo4j}

        # Obter contagens específicas no Postgres
        with conn_postgres.cursor() as cur:
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tabelas = [row[0] for row in cur.fetchall()]

            for tabela in tabelas:
                cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = cur.fetchone()[0]
                if "rel" in tabela.lower():
                    resultados_completude["postgres"].setdefault("relationships", {})[tabela] = count
                else:
                    resultados_completude["postgres"].setdefault("nodes", {})[tabela] = count

        # Exibir os resultados
        print("\n** Completude **\n")
        print("Neo4j - Nodos:")
        for labels, total in resultados_completude["neo4j"]["nodes"].items():
            print(f"  Labels: {labels} - Total: {total}")

        print("\nNeo4j - Relacionamentos:")
        for tipo, total in resultados_completude["neo4j"]["relationships"].items():
            print(f"  Tipo: {tipo} - Total: {total}")

        print("\nPostgres - Tabelas de nodos:")
        for tabela, total in resultados_completude["postgres"].get("nodes", {}).items():
            print(f"  Tabela: {tabela} - Total: {total}")

        print("\nPostgres - Tabelas de relacionamentos:")
        for tabela, total in resultados_completude["postgres"].get("relationships", {}).items():
            print(f"  Tabela: {tabela} - Total: {total}")

        # Comparar as somas totais de nodos e relacionamentos
        total_nodos_neo4j = sum(resultados_completude["neo4j"]["nodes"].values())
        total_rels_neo4j = sum(resultados_completude["neo4j"]["relationships"].values())
        total_nodos_postgres = sum(resultados_completude["postgres"].get("nodes", {}).values())
        total_rels_postgres = sum(resultados_completude["postgres"].get("relationships", {}).values())

        print("\nResumo:")
        print(f"Neo4j - Nodos: {total_nodos_neo4j}, Relacionamentos: {total_rels_neo4j}")
        print(f"Postgres - Nodos: {total_nodos_postgres}, Relacionamentos: {total_rels_postgres}")

        return total_nodos_neo4j == total_nodos_postgres and total_rels_neo4j == total_rels_postgres

    except Exception as e:
        print(f"Erro ao verificar completude: {e}")
        raise

import psycopg2
import re

def get_primary_key_columns(cur, table_name):
    query = """
    SELECT kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    WHERE tc.table_name = %s
      AND tc.constraint_type = 'PRIMARY KEY'
    ORDER BY kcu.ordinal_position;
    """
    cur.execute(query, (table_name,))
    cols = [row[0] for row in cur.fetchall()]
    return cols

def verificar_corretude(conn_postgres, conn_neo4j):
    resultados_diferentes = []

    try:
        with conn_postgres.cursor() as cur, conn_neo4j.session() as session:
            # Obter a lista de tabelas no Postgres
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tabelas_postgres = [row[0] for row in cur.fetchall()]

            # Obter os rótulos (labels) dos nodos no Neo4j com contagem
            labels_neo4j = session.run("""
                MATCH (n)
                WITH labels(n) AS tipos, count(n) AS total
                UNWIND tipos AS tipo
                RETURN tipo, total
            """).values()

            # Verificar nodos
            for label, total in labels_neo4j:
                tabela_postgres = label.lower()
                if tabela_postgres in tabelas_postgres:
                    # Obter as colunas de chave primária da tabela PostgreSQL
                    pk_cols = get_primary_key_columns(cur, tabela_postgres)
                    if pk_cols:
                        order_clause_pg = "ORDER BY " + ", ".join(pk_cols)
                        order_clause_n4j = "ORDER BY " + ", ".join([f"n.{col}" for col in pk_cols])
                    else:
                        order_clause_pg = ""
                        order_clause_n4j = ""

                    query_neo4j = f"""
                        MATCH (n:{label})
                        RETURN n
                        {order_clause_n4j}
                    """
                    # Executa a query no Neo4j e extrai os valores do dicionário retornado
                    resultado_neo4j_data = session.run(query_neo4j).data()
                    resultado_neo4j = sorted([tuple(n['n'].values()) for n in resultado_neo4j_data])

                    # Consulta no Postgres
                    cur.execute(f"SELECT * FROM {tabela_postgres} {order_clause_pg}")
                    resultado_postgres = cur.fetchall()

                    if resultado_neo4j != resultado_postgres:
                        resultados_diferentes.append({
                            "tipo": "Nodo",
                            "label": label,
                            "consulta_neo4j": query_neo4j,
                            "consulta_postgres": f"SELECT * FROM {tabela_postgres} {order_clause_pg}",
                            "neo4j": resultado_neo4j,
                            "postgres": resultado_postgres,
                        })
                    else:
                        print(f"Dados corretos para nodo: {label}")

            # Verificar relacionamentos
            # Obter os tipos de relacionamento e suas contagens no Neo4j
            rel_types_neo4j = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS tipo, count(*) AS total
            """).values()

            for rel_type, total in rel_types_neo4j:
                tabela_postgres = rel_type.lower()
                if tabela_postgres in tabelas_postgres:
                    partes = rel_type.split('_')
                    if len(partes) >= 2:
                        origem_label = partes[0]
                        destino_label = partes[-1]
                    else:
                        origem_label = tabela_postgres
                        destino_label = tabela_postgres

                    origem_table = origem_label.lower()
                    destino_table = destino_label.lower()

                    pk_origem = get_primary_key_columns(cur, origem_table)
                    pk_destino = get_primary_key_columns(cur, destino_table)
                    
                    if pk_origem and pk_destino:
                        # Utilizar a primeira coluna de cada chave primária para ordenação (para simplificação)
                        order_clause = f"ORDER BY rel.{origem_table}_{pk_origem[0]}"
                        order_clause_n4j = f"ORDER BY n.{pk_origem[0]}, m.{pk_destino[0]}"
                    else:
                        order_clause = ""
                        order_clause_n4j = ""
                    
                    query_neo4j = f"""
                        MATCH (n)-[r:{rel_type}]->(m)
                        RETURN n.{pk_origem[0]} AS origem_pk, m.{pk_destino[0]} AS destino_pk
                        {order_clause_n4j}
                    """
                    
                    # Executa a consulta no Neo4j
                    resultado_neo4j = session.run(query_neo4j).values()

                    # Consulta no Postgres com JOINs
                    query_postgres = f"""
                        SELECT origem.{pk_origem[0]}, destino.{pk_destino[0]}
                        FROM {tabela_postgres} AS rel
                        JOIN {origem_table} AS origem ON rel.{origem_table}_{pk_origem[0]} = origem.{pk_origem[0]}
                        JOIN {destino_table} AS destino ON rel.{destino_table}_{pk_destino[0]} = destino.{pk_destino[0]}
                        {order_clause}
                    """
                    cur.execute(query_postgres)
                    resultado_postgres = cur.fetchall()

                    resultado_neo4j = sorted([tuple(row) for row in resultado_neo4j])
                    resultado_postgres = sorted([tuple(row) for row in resultado_postgres])

                    if resultado_neo4j != resultado_postgres:
                        resultados_diferentes.append({
                            "tipo": "Relacionamento",
                            "label": rel_type,
                            "consulta_neo4j": query_neo4j,
                            "consulta_postgres": query_postgres,
                            "neo4j": resultado_neo4j,
                            "postgres": resultado_postgres,
                        })
                    else:
                        print(f"Dados corretos para relacionamento: {rel_type}")

        if resultados_diferentes:
            print("Diferenças encontradas:")
            for diferenca in resultados_diferentes:
                print("----------------------------------------")
                print(f"Tipo: {diferenca['tipo']}, Label: {diferenca['label']}")
                print(f"Consulta Neo4j: {diferenca['consulta_neo4j']}")
                print(f"Consulta Postgres: {diferenca['consulta_postgres']}")
                print(f"Neo4j: {diferenca['neo4j']}")
                print(f"Postgres: {diferenca['postgres']}")
            print("----------------------------------------")
        else:
            print("Nenhuma diferença encontrada.")
        
        return len(resultados_diferentes) == 0

    except Exception as e:
        print(f"Erro ao verificar corretude: {e}")
        raise

if __name__ == "__main__":
    # Carregar o dicionário
    # file_path = "GraphRel/nos_dump.pkl"
    # file_path = "GraphRel/stackoverflow.pkl"
    # file_path = "GraphRel/movie.pkl"
    file_path = "GraphRel/airbnb.pkl"

    with open(file_path, "rb") as f:
        pg_schema_dict = pickle.load(f)

    # Gerar o script SQL
    script_sql, insert_nodes_sql, insert_rel_sql = gerar_script_sql(pg_schema_dict)

    insert_nodes_sql.append("SET CLIENT_ENCODING TO 'UTF8';")

    # Salvar o script em um arquivo SQL
    with open("GraphRel/GraphRel/GraphRel/graph_to_rel.sql", "w") as f:
        f.write(script_sql)

    with open("GraphRel/GraphRel/GraphRel/insert_nodes.sql", "w", encoding="utf-8") as insert_file:
        insert_file.write("\n".join(insert_nodes_sql))

    with open("GraphRel/GraphRel/GraphRel/insert_rel.sql", "w", encoding="utf-8") as insert_file:
        insert_file.write(insert_rel_sql)

    print("Script SQL gerado com sucesso: graph_to_rel.sql")

    # Conectar ao banco de dados
    conn = conectar_postgres({**DATABASE_CONFIG, "dbname": "postgres"})

    try:
        # Criar o banco a partir do script
        criar_banco(conn, name_db, script_sql)

        # Inserir dados dos nodos
        # node_inserts = insert_nodes_sql.strip().split("\n")
        file = "GraphRel/erros_nodes.txt"
        node_inserts = insert_nodes_sql
        print("\nInicio (Nodes)\n")
        inserir_em_lotes(conn, node_inserts, BATCH_SIZE, file, MAX_LINES, name_db, DATABASE_CONFIG)
        print("\nFim (Nodes)\n")

        # # Inserir dados dos relacionamentos
        # rel_inserts = insert_rel_sql
        file = "GraphRel/erros_rel.txt"
        rel_inserts = insert_rel_sql.strip().split(";")
        # print("\nInicio (Rel)\n")
        # inserir_em_lotes(conn, rel_inserts, BATCH_SIZE, file, MAX_LINES, name_db, DATABASE_CONFIG)
        # print("\nFim (Rel)\n")

    finally:
        conn.close()
        print("Conexão com o PostgreSQL encerrada.")

    # Experimentos
    conn_postgres = psycopg2.connect(dbname="testerel", **DATABASE_CONFIG)
    conn_neo4j = GraphDatabase.driver(uri="bolt://localhost:7687", auth=("neo4j", "1F16EBD3"))

    if verificar_completude(conn_postgres, conn_neo4j):
        print("Completude: Todos os dados foram inseridos corretamente.")
    else:
        print("Completude: Discrepâncias encontradas.")

    if verificar_corretude(conn_postgres, conn_neo4j):
        print("Corretude: Os dados foram migrados corretamente.")
    else:
        print("Corretude: Diferenças encontradas nos dados.")
