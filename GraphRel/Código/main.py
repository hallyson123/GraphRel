import psycopg2
from psycopg2 import sql
from neo4j import GraphDatabase
from GraphRel import gerar_script_sql
import pickle

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
        # conectar ao banco correto
        if db_name and database_config:
            conn.close()
            conn = psycopg2.connect(dbname=db_name, **database_config)

        #Filtrar consultas vazias ou inválidas
        inserts = [query.strip() for query in inserts if query.strip()]
        
        total_processed = 0
        error_log_file = file

        # with conn.cursor() as cur:
        with open(error_log_file, "w", encoding="utf-8") as error_log, conn.cursor() as cur:
            count_error = 0
            for i in range(0, len(inserts), batch_size):
                lote = inserts[i:i + batch_size]
                
                # Verificar limite de linhas a serem processadas
                if max_lines is not None and total_processed + len(lote) > max_lines:
                    lote = lote[:max_lines - total_processed]
                    # print(i, lote)

                for line_number, query in enumerate(lote, start=i + 1):
                    try:
                        cur.execute(query)
                    except Exception as e:
                        # Registrar o erro e continuar com o próximo insert
                        # print(f"Erro na linha {line_number}: {e}")
                        # print(f"Query com erro: {query}")

                        error_log.write(f"Erro na linha {line_number}: {e}\n")
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

            error_log.write(f"Quantidade de erros: {count_error}\n")
            print(f"Erros registrados em {file}.")

    except Exception as e:
        conn.rollback()
        # print(query)
        # print(f"Erro ao inserir dados: {e}")

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

def verificar_corretude(conn_postgres, conn_neo4j):
    resultados_diferentes = []

    try:
        # Obter informações sobre tabelas e rótulos
        with conn_postgres.cursor() as cur, conn_neo4j.session() as session:
            # Obter tabelas no Postgres
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tabelas_postgres = [row[0] for row in cur.fetchall()]

            # Obter rótulos de nodos e tipos de relacionamentos no Neo4j
            labels_neo4j = session.run("""
                MATCH (n)
                WITH labels(n) AS tipos
                UNWIND tipos AS tipo
                RETURN tipo, count(*) AS total
            """).values()

            rel_types_neo4j = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) AS tipo, count(*) AS total
            """).values()

            # Verificar nodos
            for label, _ in labels_neo4j:
                tabela_postgres = label.lower()
                if tabela_postgres in tabelas_postgres:
                    # Consulta no Neo4j
                    query_neo4j = f"""
                        MATCH (n:{label})
                        RETURN *
                        ORDER BY id(n)
                    """
                    resultado_neo4j = session.run(query_neo4j).values()

                    # Consulta no Postgres
                    cur.execute(f"SELECT * FROM {tabela_postgres} ORDER BY id")
                    resultado_postgres = cur.fetchall()

                    # Comparar resultados
                    resultado_neo4j = sorted([tuple(row) for row in resultado_neo4j])
                    resultado_postgres = sorted([tuple(row) for row in resultado_postgres])

                    if resultado_neo4j != resultado_postgres:
                        resultados_diferentes.append({
                            "tipo": "Nodo",
                            "label": label,
                            "consulta_neo4j": query_neo4j,
                            "consulta_postgres": f"SELECT * FROM {tabela_postgres}",
                            "neo4j": resultado_neo4j,
                            "postgres": resultado_postgres,
                        })

            # Verificar relacionamentos com JOINs
            for rel_type, _ in rel_types_neo4j:
                tabela_postgres = rel_type.lower()
                if tabela_postgres in tabelas_postgres:
                    # Consulta no Neo4j
                    query_neo4j = f"""
                        MATCH (n)-[r:{rel_type}]->(m)
                        RETURN n.id, m.id
                        ORDER BY r
                    """
                    resultado_neo4j = session.run(query_neo4j).values()

                    # Consulta no Postgres com JOIN
                    cur.execute(f"""
                        SELECT origem.id, destino.id
                        FROM {rel_type.lower()} AS rel
                        JOIN {rel_type.split('_')[0].lower()} AS origem ON rel.origem_id = origem.id
                        JOIN {rel_type.split('_')[-1].lower()} AS destino ON rel.destino_id = destino.id
                        ORDER BY rel.id
                    """)
                    resultado_postgres = cur.fetchall()

                    # Comparar resultados
                    resultado_neo4j = sorted([tuple(row) for row in resultado_neo4j])
                    resultado_postgres = sorted([tuple(row) for row in resultado_postgres])

                    if resultado_neo4j != resultado_postgres:
                        resultados_diferentes.append({
                            "tipo": "Relacionamento",
                            "label": rel_type,
                            "consulta_neo4j": query_neo4j,
                            "consulta_postgres": f"""
                                SELECT origem.id, destino.id
                                FROM {rel_type.lower()} AS rel
                                JOIN {rel_type.split('_')[0].lower()} AS origem ON rel.origem_id = origem.id
                                JOIN {rel_type.split('_')[-1].lower()} AS destino ON rel.destino_id = destino.id
                                ORDER BY rel.id
                            """,
                            "neo4j": resultado_neo4j,
                            "postgres": resultado_postgres,
                        })

        # Exibir resultados
        if resultados_diferentes:
            print("Diferenças encontradas:")
            for diferenca in resultados_diferentes:
                print(f"Tipo: {diferenca['tipo']}, Label: {diferenca['label']}")
                print(f"Consulta Neo4j: {diferenca['consulta_neo4j']}")
                print(f"Consulta Postgres: {diferenca['consulta_postgres']}")
                print(f"Neo4j: {diferenca['neo4j']}")
                print(f"Postgres: {diferenca['postgres']}")
        else:
            print("Nenhuma diferença encontrada.")

        return len(resultados_diferentes) == 0

    except Exception as e:
        print(f"Erro ao verificar corretude: {e}")
        raise

if __name__ == "__main__":
    # Carregar o dicionário
    file_path = "GraphRel/nos_dump.pkl"
    # file_path = "GraphRel/stackoverflow.pkl"
    # file_path = "GraphRel/movie.pkl"

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
        print("\nInicio (Rel)\n")
        inserir_em_lotes(conn, rel_inserts, BATCH_SIZE, file, MAX_LINES, name_db, DATABASE_CONFIG)
        print("\nFim (Rel)\n")

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
