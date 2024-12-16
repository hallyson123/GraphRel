from GraphRel import gerar_script_sql
from migra import insert_nodes
import pickle

ARRAY_LIST = True
DUAS_TABELAS_CASO_DOIS = False
LISTA_COMO_TABELA = True

# Carregar o dicionário
file_path = "GraphRel/nos_dump.pkl"

with open(file_path, "rb") as f:
    pg_schema_dict = pickle.load(f)

# Gerar o script SQL
script_sql, insert_nodes_sql, insert_rel_sql = gerar_script_sql(pg_schema_dict)

# insert_sql_um = insert_nodes(pg_schema_dict)

# Salvar o script em um arquivo SQL
with open("GraphRel/GraphRel/GraphRel/graph_to_rel.sql", "w") as f:
    f.write(script_sql)

# with open("GraphRel/GraphRel/GraphRel/insert_data.sql", "w") as insert_file:
#     insert_file.write(insert_sql)

with open("GraphRel/GraphRel/GraphRel/insert_nodes.sql", "w", encoding="utf-8") as insert_file:
    insert_file.write(insert_nodes_sql)

with open("GraphRel/GraphRel/GraphRel/insert_rel.sql", "w", encoding="utf-8") as insert_file:
    insert_file.write(insert_rel_sql)

print("Script SQL gerado com sucesso: graph_to_rel.sql")
