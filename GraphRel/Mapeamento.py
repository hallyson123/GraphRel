from neo4j import GraphDatabase
import psycopg2

# Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "1F16EBD3"

# Postgres
POSTGRES_URI = "dbname='teste' user='postgres' host='localhost' password='1F16EBD3'"

# Extrair dados do Neo4j
def extrair_dados_neo4j():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    graph_data = {"nodes": {}, "relationships": []}
    
    with driver.session() as session:
        # Consultar nodos
        nodes_query = "MATCH (n) RETURN labels(n) as labels, properties(n) as props"
        result = session.run(nodes_query)
        for record in result:
            labels = "_".join(record["labels"])
            if labels not in graph_data["nodes"]:
                graph_data["nodes"][labels] = []
            graph_data["nodes"][labels].append(record["props"])
        
        # Consultar relacionamentos
        rel_query = """
        MATCH (a)-[r]->(b)
        RETURN type(r) as type, startNode(r).id as origin, endNode(r).id as destination, properties(r) as props
        """
        result = session.run(rel_query)
        for record in result:
            graph_data["relationships"].append({
                "type": record["type"],
                "origin": record["origin"],
                "destination": record["destination"],
                "properties": record["props"]
            })
    
    driver.close()
    # print(graph_data["nodes"])
    return graph_data

# Inserir dados no relacional
def inserir_dados_relacional(graph_data):
    conn = psycopg2.connect(POSTGRES_URI)
    cur = conn.cursor()

    # Inserir nodos
    for label, nodes in graph_data["nodes"].items():
        table_name = label.lower()
        for node in nodes:
            columns = []
            values = []
            
            for key, value in node.items():
                if isinstance(value, list):
                    # Inserir lista em tabela auxiliar
                    aux_table_name = f"{table_name}_{key}_list"
                    for item in value:
                        cur.execute(f"INSERT INTO {aux_table_name} ({table_name}_id, {key}) VALUES (%s, %s);", 
                                    (node['id'], item))
                # elif isinstance(value, str) and value.startswith("enum:"):
                #     continue
                else:
                    columns.append(key)
                    values.append(value)
            
            if columns:
                columns_str = ", ".join(columns)
                values_str = ", ".join([f"%s" for _ in values])
                cur.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});", values)

    # Inserir relacionamentos
    for rel in graph_data["relationships"]:
        table_name = f"{rel['type'].lower()}_rel"
        columns = ["origin", "destination"]
        values = [rel["origin"], rel["destination"]]

        for key, value in rel["properties"].items():
            if isinstance(value, list):
                # Inserir lista em tabela auxiliar
                aux_table_name = f"{table_name}_{key}_list"
                for item in value:
                    cur.execute(f"INSERT INTO {aux_table_name} ({table_name}_id, {key}) VALUES (%s, %s);", 
                                (rel['id'], item))
            # elif isinstance(value, str) and value.startswith("enum:"):
            #     continue
            else:
                columns.append(key)
                values.append(value)

        columns_str = ", ".join(columns)
        values_str = ", ".join([f"%s" for _ in values])
        cur.execute(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});", values)

    conn.commit()
    cur.close()
    conn.close()

# Verificar completude e corretude
# def teste_validacao():

graph_data = extrair_dados_neo4j()
inserir_dados_relacional(graph_data)
# teste_validacao()
