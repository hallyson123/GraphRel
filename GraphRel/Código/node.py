from auxiliar import modificar_tipos

LISTA_COMO_TABELA = True

PALAVRAS_RESERVADAS = ["user"]

def tratamento_node(script_sql, insert_sql, pg_schema_dict):
    # Criar tabelas para os nodos
    script_sql += "/*Criando tabelas com atributos, tipos e PK*/\n"
    # insert_sql += "/*Inserts para popular as tabelas*/\n"

    insert_sql = []

    nodos_com_um_rotulo = []
    nodos_com_multiplos_rotulos = []

    aux_sql_list = ""

    # Separando os nodos com um rótulo e com múltiplos rótulos
    for node_name, node_data in pg_schema_dict["nodes"].items():
        if len(node_name) == 1:
            nodos_com_um_rotulo.append((node_name, node_data))
        else:
            nodos_com_multiplos_rotulos.append((node_name, node_data))

    # Criar tabelas para nodos com **um** rótulo
    for node_name, node_data in nodos_com_um_rotulo:
        node = ''.join(node_name)
        tabela_nome = node.lower()

        # Verificar se o nome da tabela é uma palavra reservada
        if tabela_nome in PALAVRAS_RESERVADAS:
            tabela_nome += "_table"

        script_sql += f"CREATE TABLE {tabela_nome} (\n"
        primary_key_set = False

        if not node_data["uniqueProperties"]:
            script_sql += "  id SERIAL PRIMARY KEY,\n"
            node_data["primary_key_info"] = [{"nome_propriedade": "id", "nome_chave": "id", "tipo_propriedade": "INTEGER", "composta": False, "valores_propriedade": None}]
            primary_key_set = True

        for prop, prop_data in node_data["properties"].items():
            tipo = prop_data["type"]
            tipo = modificar_tipos(tipo, prop_data)

            tipo_fk = []
            if node_data["uniqueProperties"] and not primary_key_set:
                tipo_aux = pg_schema_dict["nodes"][node_name]['properties'][prop]['type']
                tipo_fk.append(tipo_aux.upper())

            # lista vira array
            if LISTA_COMO_TABELA == False:
                if prop_data['type'] == 'array':
                    tipo = prop_data['typeList']
                    # tipo = f"VARCHAR(1000)" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    tipo = f"VARCHAR" if tipo == "str" else ("BIGINT" if tipo == "int" else "REAL")
                    tipo += "[]"
                    if prop_data["unique"]:
                        tipo += " UNIQUE"
                    if not prop_data["optional"]:
                        tipo += " NOT NULL"

                    script_sql += f"  {prop} {tipo},\n"
                else:
                    script_sql += f"  {prop} {tipo.upper()},\n"
            else: 
                if prop_data['type'] != 'array':
                    script_sql += f"  {prop} {tipo.upper()},\n"

        # Definir chave primaria (unica ou composta)
        if node_data["uniqueProperties"] and not primary_key_set:
            node_data["primary_key_info"] = []

            # Chave unica
            if len(node_data["uniqueProperties"]) == 1:
                prop_primary = node_data["uniqueProperties"][0]
                valor_propriedade = node_data["properties"][prop_primary]["insert_values"]
                # print(prop_primary, valor_propriedade)
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({prop_primary}) \n"
                node_data["primary_key_info"].append({"nome_propriedade": prop_primary, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": False, "valores_propriedade": valor_propriedade})
            
            else:
                chave_composta = node_data["uniqueProperties"]
                chave_composta_str = ", ".join(chave_composta)
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({chave_composta_str}) \n"
                # print(chave_composta)

                for prop in chave_composta:
                    valor_propriedade = node_data["properties"][prop]["insert_values"]
                    if ({"nome_propriedade": chave_composta_str, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True}) not in node_data["primary_key_info"]:
                        node_data["primary_key_info"].append({"nome_propriedade": chave_composta_str, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True})
            
            primary_key_set = True

        script_sql = script_sql.rstrip(",\n")
        script_sql += "\n);\n\n"

#########################

        # Gerar inserts para o nodo
        attributes = []
        for prop, prop_data in node_data["properties"].items():
            if prop_data["type"] != "array":
                attributes.append(prop)

        valores_por_coluna = []

        max_length = 0
        for prop, prop_data in node_data["properties"].items():
            if LISTA_COMO_TABELA:
                if prop_data["type"] != "array":
                    valores_por_coluna.append(prop_data["insert_values"])   
                    # print(valores_por_coluna)
                    max_length = max(max_length, len(prop_data["insert_values"]))
            else:
                print("TRATAR LIST")

        valores_por_coluna = [
            col + [None] * (max_length - len(col)) for col in valores_por_coluna
        ]

        registros = zip(*valores_por_coluna)

        # Gerar os comandos INSERT
        for registro in registros:
            columns = ", ".join(attributes)
            values_list = []

            for i, v in enumerate(registro):
                # Obter o nome do atributo
                prop_name = attributes[i]
                prop_data = node_data["properties"][prop_name]

                # Tratar o valor com base no tipo esperado
                tipo = prop_data["type"]

                if v == "deleted":
                    print(prop_name, v)

                if v is None:
                    values_list.append('NULL')
                elif tipo == "str":
                    values_list.append(f"'{v}'")
                elif tipo == "int":
                    values_list.append(str(v))
                elif tipo == "float":
                    values_list.append(f"{v:.2f}")  # Formatar floats com duas casas decimais (se necessário)
                elif tipo == "bool":
                    values_list.append('TRUE' if v else 'FALSE')
                else:
                    values_list.append(f"'{v}'")  # Caso padrão (trata como string)

            values = ", ".join(values_list)
            if values == "'user899621', deleted":
                print(values)
            # insert_sql += f"INSERT INTO {tabela_nome} ({columns}) VALUES ({values});\n"
            insert_sql.append(f"INSERT INTO {tabela_nome} ({columns}) VALUES ({values});")

# #########################

        # Tratar tipo list (criar tabela ou virar array)
        for prop, prop_data in node_data["properties"].items():
            tipo = prop_data["typeList"]
            origem_info = pg_schema_dict['nodes'][node_name]['primary_key_info']

            if (prop_data["type"] == 'array'):
                tipo_lista = modificar_tipos(tipo, prop_data)

                if LISTA_COMO_TABELA:
                    tipo_lista_nome = f"{tabela_nome}_{prop}_list"
                    aux_sql_list += f"CREATE TABLE {tipo_lista_nome} (\n"

                    for pk in origem_info:
                        # print(pk)
                        nome_propriedade = pk['nome_propriedade']
                        nome_propriedade = nome_propriedade.split(", ") # Divide a string em uma lista pra percorrer uma chave por vez
                        
                        if pk['composta']:
                            for nome in nome_propriedade:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][nome]['type']
                                tipo = modificar_tipos(tipo, prop_data)
                                aux_sql_list += f"  {tabela_nome}_{nome}_id {tipo},\n"

                            aux_sql_list += f"  {prop} {tipo_lista.upper()},\n"

                            for nome in nome_propriedade:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][nome]['type']
                                tipo = modificar_tipos(tipo, prop_data)
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome}_id) REFERENCES {tabela_nome}({nome})"

                                # Virgula apenas se não for o último elemento
                                if nome != nome_propriedade[-1]:
                                    aux_sql_list += ",\n"
                                else:
                                    aux_sql_list += "\n"

                            aux_sql_list += ");\n\n"

                        else:
                            if pk['nome_propriedade'] == 'id':
                                aux_sql_list += f"  {tabela_nome}_{nome_propriedade} ({pk['tipo_propriedade']}),\n"
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome_propriedade}) REFERENCES {tabela_nome}({nome_propriedade}),\n"
                            else:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][pk['nome_propriedade']]['type']
                                aux_sql_list += f"  {tabela_nome}_{nome_propriedade} ({pk['tipo_propriedade']}),\n"
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome_propriedade}) REFERENCES {tabela_nome}({nome_propriedade}),\n"

    script_sql += aux_sql_list

##########################################################################
##########################################################################

    # Criar tabelas para nodos com **mais de um** rótulo
    for node_name, node_data in nodos_com_multiplos_rotulos:
        node = '_'.join(node_name)
        tabela_nome = node.lower()

        tipo_enum_filhos = f"{tabela_nome}_tipo_enum"
        #script_sql += f"CREATE TYPE {tipo_enum_filhos.upper()} AS ENUM({', '.join([f'\'{child_label}\'' for child_label in node_name])});\n\n"

        # Flag para especialização
        node_data['is_spec'] = True

        script_sql += f"CREATE TABLE {tabela_nome} (\n"
        primary_key_set = False

        if not node_data["uniqueProperties"]:
            script_sql += "  id SERIAL PRIMARY KEY,\n"
            node_data["primary_key_info"] = [{"nome_propriedade": "id", "nome_chave": "id", "tipo_propriedade": "INTEGER", "composta": False, "valores_propriedade": None}]
            primary_key_set = True

        # script_sql += f"  tipo {tipo_enum_filhos.upper()},\n"

        for prop, prop_data in node_data["properties"].items():
            tipo = prop_data["type"]
            tipo = modificar_tipos(tipo, prop_data)

            tipo_fk = []
            if node_data["uniqueProperties"] and not primary_key_set:
                tipo_aux = pg_schema_dict["nodes"][node_name]['properties'][prop]['type']
                tipo_fk.append(tipo_aux.upper())

            # lista vira array
            if LISTA_COMO_TABELA == False:
                if prop_data['type'] == 'array':
                    tipo = prop_data['typeList']
                    # tipo = f"VARCHAR(1000)" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    tipo = f"VARCHAR" if tipo == "str" else ("BIGINT" if tipo == "int" else "REAL")
                    tipo += "[]"
                    if prop_data["unique"]:
                        tipo += " UNIQUE"
                    if not prop_data["optional"]:
                        tipo += " NOT NULL"

                    script_sql += f"  {prop} {tipo},\n"
            else: 
                if prop_data['type'] != 'array':
                    script_sql += f"  {prop} {tipo.upper()},\n"

        # Definir chave primaria (unica ou composta)
        if node_data["uniqueProperties"] and not primary_key_set:
            node_data["primary_key_info"] = []
            if len(node_data["uniqueProperties"]) == 1:
                prop_primary = node_data["uniqueProperties"][0]
                valor_propriedade = node_data["properties"][prop_primary]["insert_values"]
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({prop_primary}) \n"
                
                node_data["primary_key_info"].append({"nome_propriedade": prop_primary, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": False, "valores_propriedade": valor_propriedade})
            
            # else:
            #     chave_composta = node_data["uniqueProperties"]
            #     script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({chave_composta}), \n"

            #     node_data["primary_key_info"].append({"nome_propriedade": chave_composta, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True})

            else:
                chave_composta = node_data["uniqueProperties"]
                chave_composta_str = ", ".join(chave_composta)
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({chave_composta_str}) \n"
                # print(chave_composta)

                for prop in chave_composta:
                    valor_propriedade = node_data["properties"][prop]["insert_values"]

                    if ({"nome_propriedade": chave_composta_str, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True}) not in node_data["primary_key_info"]:
                        node_data["primary_key_info"].append({"nome_propriedade": chave_composta_str, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True})
            
            primary_key_set = True

        script_sql = script_sql.rstrip(",\n")
        script_sql += "\n);\n\n"

#####################################

        # Gerar inserts para o nodo
        attributes = []
        for prop, prop_data in node_data["properties"].items():
            if prop_data["type"] != "array":
                attributes.append(prop)

        valores_por_coluna = []

        max_length = 0
        for prop, prop_data in node_data["properties"].items():
            if LISTA_COMO_TABELA:
                if prop_data["type"] != "array":
                    valores_por_coluna.append(prop_data["insert_values"])   
                    max_length = max(max_length, len(prop_data["insert_values"]))
            else:
                print("TRATAR LIST")

        valores_por_coluna = [
            col + [None] * (max_length - len(col)) for col in valores_por_coluna
        ]

        registros = zip(*valores_por_coluna)

        # Gerar os comandos INSERT
        for registro in registros:
            columns = ", ".join(attributes)
            values_list = []

            for i, v in enumerate(registro):
                # Obter o nome do atributo
                prop_name = attributes[i]
                prop_data = node_data["properties"][prop_name]

                # Tratar o valor com base no tipo esperado
                tipo = prop_data["type"]

                if v is None:
                    values_list.append('NULL')
                elif tipo == "str":
                    values_list.append(f"'{v}'")
                elif tipo == "int":
                    values_list.append(str(v))
                elif tipo == "float":
                    values_list.append(f"{v:.2f}")  # Formatar floats com duas casas decimais (se necessário)
                elif tipo == "bool":
                    values_list.append('TRUE' if v else 'FALSE')
                elif tipo == "Date":
                    values_list.append(f"'{v}'")
                else:
                    values_list.append(f"'{v}'")  # Caso padrão (trata como string)

            values = ", ".join(values_list)
            # insert_sql += f"INSERT INTO {tabela_nome} ({columns}) VALUES ({values});\n"
            insert_sql.append(f"INSERT INTO {tabela_nome} ({columns}) VALUES ({values});")

###############################

        # Tratar tipo list (criar tabela ou virar array)
        for prop, prop_data in node_data["properties"].items():
            tipo = prop_data["typeList"]
            origem_info = pg_schema_dict['nodes'][node_name]['primary_key_info']

            if (prop_data["type"] == 'array'):
                tipo_lista = modificar_tipos(tipo, prop_data)
                if LISTA_COMO_TABELA:
                    tipo_lista_nome = f"{tabela_nome}_{prop}_list"
                    aux_sql_list += f"CREATE TABLE {tipo_lista_nome} (\n"

                    for pk in origem_info:
                        nome_propriedade = pk['nome_propriedade']
                        
                        if pk['composta']:
                            for nome in nome_propriedade:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][nome]['type']
                                tipo = modificar_tipos(tipo, prop_data)
                                aux_sql_list += f"  {tabela_nome}_{nome}_id {tipo},\n"

                            aux_sql_list += f"  {prop} {tipo_lista.upper()},\n"

                            for nome in nome_propriedade:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][nome]['type']
                                tipo = modificar_tipos(tipo, prop_data)
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome}_id) REFERENCES {tabela_nome}({nome}),\n"

                            aux_sql_list += ");\n\n"

                        else:
                            if pk['nome_propriedade'] == 'id':
                                aux_sql_list += f"  {tabela_nome}_{nome_propriedade} ({pk['tipo_propriedade']}),\n"
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome_propriedade}) REFERENCES {tabela_nome}({nome_propriedade}),\n"
                            else:
                                tipo = pg_schema_dict["nodes"][node_name]['properties'][pk['nome_propriedade']]['type']
                                aux_sql_list += f"  {tabela_nome}_{nome_propriedade} ({pk['tipo_propriedade']}),\n"
                                aux_sql_list += f"  FOREIGN KEY ({tabela_nome}_{nome_propriedade}) REFERENCES {tabela_nome}({nome_propriedade}),\n"

    script_sql += "/*Finalizada a criacao de tabelas (e especializacoes)*/\n\n"

    return script_sql, insert_sql