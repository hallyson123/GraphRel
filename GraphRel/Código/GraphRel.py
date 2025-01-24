from auxiliar import modificar_tipos
from rel import tratamento_rel
from node import tratamento_node

LISTA_COMO_TABELA = True

# gerar o script SQL
def gerar_script_sql(pg_schema_dict):
    script_sql = ""
    insert_nodes_sql = ""
    insert_rel_sql = ""

    aux_sql_list = ""

    # script_sql += "CREATE DATABASE testerel; \n"
    # script_sql += "\c testerel\n"

    # Criar tipo ENUM (nodos)
    for node_name, node_data in pg_schema_dict["nodes"].items():
        for prop, prop_data in node_data["properties"].items():
            if prop_data["is_enum"]:
                node = ''.join(node_name)
                tipo_enum = f"{node}_{prop}_enum"
                prop_data["typeEnum"] = tipo_enum
                # script_sql += f"CREATE TYPE {tipo_enum.upper()} AS ENUM({prop_data['values']});\n"

                # USAR DEPOIS
                # script_sql += f"CREATE TYPE {tipo_enum_filhos.upper()} AS ENUM({', '.join([f'\'{child_label}\'' for child_label in node_name])});\n\n"

    script_sql += "\n"

    # Criar tipo ENUM (relacionamentos)
    for rel in pg_schema_dict["relationships"]:
        rel_name = rel["relationship_type"].lower()
        origem = '_'.join(rel["origin"]).lower()
        destino = '_'.join(rel["destination"]).lower()
        rel_table = f"{origem}_{rel_name}Rel_{destino}"

        for prop, prop_data in rel["properties"].items():
            if prop_data["is_enum"]:
                tipo_enum = f"{rel_table}_{prop}_enum"
                prop_data["typeEnum"] = tipo_enum

                # print(prop_data['valores_enum'])

                # Adiciona aspas simples a cada valor no array
                valores_com_aspas = [f"'{valor}'" for valor in prop_data['valores_enum']]
        
                # Junta os valores com vírgulas
                valores_formatados = ", ".join(valores_com_aspas)

                # print(valores_formatados)

                # script_sql += f"CREATE TYPE {tipo_enum.upper()} AS ENUM({valores_formatados});\n"

    script_sql += "\n"

    script_sql, insert_nodes_sql = tratamento_node(script_sql, insert_nodes_sql, pg_schema_dict)

    script_sql, insert_rel_sql = tratamento_rel(script_sql, insert_rel_sql, pg_schema_dict)
        
    return script_sql, insert_nodes_sql, insert_rel_sql
