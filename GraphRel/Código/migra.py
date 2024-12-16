import psycopg2

def insert_nodes(pg_schema_dict):

    for node_name, node_data in pg_schema_dict["nodes"].items(): 
        table_name = '_'.join(node_name).lower()  # Nome da tabela
        attributes = list(node_data["properties"].keys())  # Obter as colunas da tabela

        # Coletar valores para cada coluna
        valores_por_coluna = [prop_data['insert_values'] for prop_data in node_data["properties"].values()]

        # Combinar os valores em registros completos
        registros = zip(*valores_por_coluna)

        # Gerar os comandos INSERT
        for registro in registros:
            columns = ", ".join(attributes)
            values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in registro])  # Formatar os valores
            sql_query = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
            # sql_query += "\n\n****************************************************************\n\n"
            # print(sql_query)  # Verificar antes de executar

    return sql_query

# INSERT INTO person_director (tipo, born, bornIn, tmdbId, bio, died, name, imdbId, url, poster) VALUES ('Person', '1962-10-09', ' Detroit, Michigan, USA', '31211', 'From Wikipedia, the free encyclopedia. Anthony Waller (born October 24, 1959)', '2009-04-02', 'Clive Barker', '0323787', 'https://themoviedb.org/person/31211', 'https://image.tmdb.org/t/p/w440_and_h660_face/dzHC2LxmarkBxWLhjp2DRa5oCev.jpg');


        # # Gerar inserts para o nodo
        # attributes = list(node_data["properties"].keys())
        # valores_por_coluna = []

        # for prop, prop_data in node_data["properties"].items():
        #     # Garantir que 'insert_values' seja uma lista e que todos os valores estejam preenchidos
        #     if "insert_values" in prop_data and isinstance(prop_data["insert_values"], list):
        #         valores_por_coluna.append(prop_data["insert_values"])
        #         # print(tabela_nome, prop)
        #         # if tabela_nome == "movie":
        #         #     print(prop_data["insert_values"])

        # # Combinar valores para formar registros completos
        # registros = zip(*valores_por_coluna)

        # for registro in registros:
        #     columns = ", ".join(attributes)
        #     print(registro)
        #     values = ", ".join([f"'{v}'" if isinstance(v, str) else ('NULL' if v is None else str(v)) for v in registro])
            # insert_sql += f"INSERT INTO {tabela_nome} ({columns}) VALUES ({values});\n"

                # elif tipo == "array":
                #     array_values = ', '.join(f"'{x}'" if isinstance(x, str) else str(x) for x in v)
                #     values_list.append(f"ARRAY[{array_values}]")  # Arrays formatados