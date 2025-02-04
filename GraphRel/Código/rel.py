DUAS_TABELAS_CASO_DOIS = False
LISTA_COMO_TABELA = True

PALAVRAS_RESERVADAS = ["user"]

def tratamento_rel(script_sql, insert_sql, pg_schema_dict):

    script_sql += "/*######################################################*/\n\n"

    script_sql += "/*Inicio de tratamento de relacionamentos:*/\n"
    # Adicionar relacionamentos
    for rel in pg_schema_dict["relationships"]:
        rel_name = rel["relationship_type"].lower()
        origem = '_'.join(rel["origin"]).lower()
        destino = '_'.join(rel["destination"]).lower()

        # print(pg_schema_dict["relationships"])

        origem_info = pg_schema_dict["nodes"][rel["origin"]]["primary_key_info"]
        destino_info = pg_schema_dict["nodes"][rel["destination"]]["primary_key_info"] #VERIFICAR PQ N APARECE O DESTINO
        # print(origem_info)
        # print(destino_info)

        # Interpreta a cardinalidade para definir as constraints
        # origem_card, destino_card = rel["cardinality"].split(';')
        destino_card, origem_card = rel["cardinality"].split(';')
        origem_min, origem_max = origem_card[1:-1].split(':')
        destino_min, destino_max = destino_card[1:-1].split(':')

        if origem in PALAVRAS_RESERVADAS:
            origem += "_table"
        if destino in PALAVRAS_RESERVADAS:
            destino += "_table"

        rel_table = f"{origem.upper()}_{rel_name}_{destino.upper()}"

        # Propriedades do relacionamentos
        properties_rel = ""
        for prop, prop_data in rel["properties"].items():
            # print(prop)
            if prop_data["is_enum"]:
                print("")
                # tipo = f"{prop_data['typeEnum']}"
                
                if prop == "rating":
                    tipo = "REAL"
                
            else:
                if prop_data["is_list"]:
                    tipo = prop_data['list_info']['tipo_item']
                    tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    tipo += '[]'
                else:
                    tipo = ','.join(prop_data["tipos"])
                    tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")

            # Adicionar constraints de unicidade ou obrigatoriedade
            if prop_data.get("is_singleton") and not prop_data["is_enum"]:
                tipo += " UNIQUE"
            # if prop_data.get("is_mandatory") and not prop_data["is_enum"]:
            #     tipo += f" NOT NULL"

            properties_rel += f"  {prop} {tipo.upper()},\n"

        # MUITOS PARA MUITOS (N:N)
        if origem_max == "N" and destino_max == "N" and origem != destino:
            # Marcar a cardinalidade no dicionário
            rel["cardinality_type"] = "N:N"

            # print("N:N")
            script_sql += "/*Criacao de rel (N:N)*/\n"
            script_sql += f"CREATE TABLE {rel_table} (\n"

            foreign_keys = ""

            # Chaves estrangeiras para origem e destino (criar colunas)
            for pk in origem_info:
                nome_propriedade = pk['nome_propriedade']
                nome_propriedade = nome_propriedade.split(", ")

                if pk['composta']:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][nome]['type']
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome}) REFERENCES {origem}({nome}),\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"  {origem}_id {pk['tipo_propriedade']},\n"
                        nome_propriedade = "".join(nome_propriedade)
                        foreign_keys += ",\n"
                        foreign_keys += f"  FOREIGN KEY ({origem}_{nome_propriedade}) REFERENCES {origem}({pk['nome_propriedade']}),\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][pk['nome_propriedade']]['type']
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        nome_propriedade = "".join(nome_propriedade)
                        script_sql += f"  {pk['nome_chave']}_{nome_propriedade} {tipo.upper()},\n"

                        foreign_keys += ",\n"

                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome_propriedade}) REFERENCES {origem}({pk['nome_propriedade']}),\n"

            for pk in destino_info:
                nome_propriedade = pk['nome_propriedade']
                nome_propriedade = nome_propriedade.split(", ")
                if pk['composta']:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][nome]['type']
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome}) REFERENCES {destino}({nome}),\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"  {destino}_id {pk['tipo_propriedade']},\n"
                        foreign_keys += f"  FOREIGN KEY ({destino}_{nome_propriedade}) REFERENCES {destino}({pk['nome_propriedade']}),\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][pk['nome_propriedade']]['type']
                        nome_propriedade = "".join(nome_propriedade)
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome_propriedade} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome_propriedade}) REFERENCES {destino}({pk['nome_propriedade']}),\n"

            script_sql += properties_rel.rstrip(",\n")
            script_sql += foreign_keys.rstrip(",\n")
            script_sql += "\n);\n"

            script_sql += "/*Criacao de rel (N:N) finalizada*/\n\n"

####################################################################################################

        # # TRATAR AUTORELACIONAMENTO
        # elif origem == destino:
        #     script_sql += "/*Criacao de Autorelacionamento*/\n"
        #     # print("AUTO")
        #     for pk in origem_info:
        #         nome_propriedade = pk['nome_propriedade']
        #         if pk['composta']:
        #             for nome in nome_propriedade:
        #                 tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome]['type']
        #                 tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin_{nome} {tipo},\n"
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination_{nome} {tipo},\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({nome}),\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({nome});\n\n"
        #         else:
        #             if pk['nome_propriedade'] == 'id':
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin INTEGER,\n"
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination INTEGER,\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({pk['nome_propriedade']}),\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({pk['nome_propriedade']});\n\n"
        #             else:
        #                 tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][pk['nome_propriedade']]['type']
        #                 tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin {tipo},\n"
        #                 script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination {tipo},\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({nome_propriedade}),\n"
        #                 script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({nome_propriedade});\n\n"

        #     script_sql += "/*Criacao de Autorelacionamento finalizado*/\n\n"

####################################################################################################

        elif origem_max == "N" and destino_max == "1":  # 1:N
            # print("1:N")
            rel["cardinality_type"] = "1:N"
            script_sql += "/*Criacao de rel (1:N)*/\n"
            for pk in origem_info:
                nome_propriedade = pk['nome_propriedade']
                if pk["composta"]:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome]['type']
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_{nome} {tipo};\n"
                        script_sql += f"ALTER TABLE {destino} ADD FOREIGN KEY ({origem}_{nome}) REFERENCES {origem}({nome});\n\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_id INTEGER;\n"
                        script_sql += f"ALTER TABLE {destino} ADD FOREIGN KEY ({origem}_id) REFERENCES {origem}(id);\n\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome_propriedade]['type']
                        tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_{nome_propriedade} {tipo};\n"
                        script_sql += f"ALTER TABLE {destino} ADD FOREIGN KEY ({origem}_{nome_propriedade}) REFERENCES {origem}({nome_propriedade});\n\n"
            
            script_sql += "/*Finalizado criacao de rel (1:N)*/\n\n"

        elif origem_max == "1" and destino_max == "N":  # N:1
            rel["cardinality_type"] = "N:1"
            script_sql += "/*Criacao de rel (N:1)*/\n"
            # print("N:1")
            for pk_origem in origem_info:
                nome_propriedade_origem = pk_origem['nome_propriedade']
                nome_chave_origem = pk_origem['nome_chave']
                tipo_propriedade_origem = pk_origem['tipo_propriedade']
                composta_origem = pk_origem['composta']

            for pk_destino in destino_info:
                nome_propriedade_destino = pk_destino['nome_propriedade']
                nome_chave_destino = pk_destino['nome_chave']
                tipo_propriedade_destino = pk_destino['tipo_propriedade']
                composta_destino = pk_destino['composta']

            if pk_destino["composta"]:
                # TESTAR
                for nome in nome_propriedade_destino:
                    tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][nome]['type']
                    tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_{nome} {tipo};\n"
                    script_sql += f"ALTER TABLE {origem} ADD FOREIGN KEY ({destino}_{nome}) REFERENCES {destino}({nome});\n\n"
            else:
                if pk_destino['nome_propriedade'] == 'id':
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_id INTEGER;\n"
                    script_sql += f"ALTER TABLE {origem} ADD FOREIGN KEY ({destino}_id) REFERENCES {destino}(id);\n\n"
                else:
                    tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][nome_propriedade_destino]['type']
                    tipo = f"VARCHAR" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_{nome_propriedade_destino} {tipo};\n"
                    script_sql += f"ALTER TABLE {origem} ADD FOREIGN KEY ({destino}_{nome_propriedade_destino}) REFERENCES {destino}({nome_propriedade_destino});\n\n"
    
            script_sql += "/*Criacao de rel (N:1) finalizado*/\n\n"

####################################################################################################

        # elif origem_max == "1" and destino_max == "1":
        #     if DUAS_TABELAS_CASO_DOIS and rel['more_occurrence'] != None:
        #         # Caso 2: Baixa ocorrência. Um dos rótulos tem mais ocorrência que o outro.
        #         # Cria-se duas tabelas, aquela que representa o rótulo com menor ocorrência recebe a chave do maior.

        #         # print('(1:1) DUAS TABELA')
                
        #         rotulo_mais_ocorrencia = tuple(rel['more_occurrence'])
        #         origem_key = tuple(rel["origin"])
        #         destino_key = tuple(rel["destination"])
        #         propriedades_origem = pg_schema_dict["nodes"][origem_key]['properties']
        #         propriedades_destino = pg_schema_dict["nodes"][destino_key]['properties']

        #         # print(origem_key, destino_key, rotulo_mais_ocorrencia)

        #         # Definindo qual é o lado com maior ocorrência e qual é o lado com menor ocorrência
        #         if rotulo_mais_ocorrencia == origem_key:
        #             tabela_principal = origem
        #             tabela_dependente = destino
        #             propriedades_principal = propriedades_origem
        #             propriedades_dependente = propriedades_destino
        #         else:
        #             tabela_principal = destino
        #             tabela_dependente = origem
        #             propriedades_principal = propriedades_destino
        #             propriedades_dependente = propriedades_origem

        #         # Criando a tabela para o lado principal
        #         script_sql += f"CREATE TABLE {tabela_principal} (\n"
        #         for nome, info in propriedades_principal.items():
        #             script_sql += f"  {nome} {info['type'].upper()}"
                    
        #             if info['unique']:
        #                 script_sql += " UNIQUE"
        #             if info['optional'] == False:
        #                 script_sql += " NOT NULL"
        #             script_sql += ",\n"
                
        #         # Definindo a chave primária do lado principal
        #         script_sql += "  id SERIAL PRIMARY KEY\n"
        #         script_sql += ");\n\n"

        #         # Criando a tabela para o lado dependente com chave estrangeira referenciando o principal
        #         script_sql += f"CREATE TABLE {tabela_dependente} (\n"
        #         for nome, info in propriedades_dependente.items():
        #             script_sql += f"  {nome} {info['type'].upper()}"
                    
        #             if info['unique']:
        #                 script_sql += " UNIQUE"
        #             if info['optional'] == False:
        #                 script_sql += " NOT NULL"
        #             script_sql += ",\n"
                
        #         # Adicionando chave estrangeira no lado dependente
        #         script_sql += f"  {tabela_principal}_id INTEGER REFERENCES {tabela_principal}(id)\n"
        #         script_sql += ");\n\n"

        #     else:
        #         # Caso 1: Alta ocorrência, criar tabela unificada
        #         if rel["merge"]:
        #             # print('(1:1) UNIFICAR TABELAS')
        #             script_sql += "/*Criacao de rel (1:1) (Unificar nodos)*/\n"
        #             origem_key = tuple(rel["origin"])
        #             destino_key = tuple(rel["destination"])
        #             propriedades_origem = pg_schema_dict["nodes"][origem_key]['properties']
        #             propriedades_destino = pg_schema_dict["nodes"][destino_key]['properties']
        #             # print(propriedades_origem)
        #             # print(propriedades_destino)

        #             # Define o nome da tabela: com com mais propriedades é a principal, se for igual escolhe uma (origem)
        #             if len(pg_schema_dict["nodes"][origem_key]['properties']) >= len(pg_schema_dict["nodes"][destino_key]['properties']):
        #                 table_name = origem
        #             else:
        #                 table_name = destino

        #             script_sql += f"CREATE TABLE {table_name}_unificada (\n"
                    
        #             # Adiciona colunas da tabela de origem
        #             for nome, info in propriedades_origem.items():
        #                 tipo = info['type']
        #                 tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
        #                 script_sql += f"  {nome}_{origem} {tipo.upper()}"

        #                 if info['unique']:
        #                     script_sql += " UNIQUE"

        #                 if info['optional'] == False:
        #                     script_sql += " NOT NULL,\n"

        #             # Adiciona colunas da tabela de destino
        #             for nome, info in propriedades_destino.items():
        #                 tipo = info['type']
        #                 tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
        #                 script_sql += f"  {nome}_{destino} {tipo.upper()}"

        #                 if info['unique']:
        #                     script_sql += " UNIQUE"
                            
        #                 if info['optional'] == False:
        #                     script_sql += " NOT NULL,\n"
                    
        #             # # Define a chave primária origem
        #             pk_create = False
        #             primary_key = "  id SERIAL PRIMARY KEY, "
        #             script_sql_pk = ""

        #             for nome, info in propriedades_origem.items():
        #                 if (info['optional'] == False) and (info['unique'] == True):
        #                     script_sql_pk += f"  CONSTRAINT pk_{origem}_{nome} PRIMARY KEY ({nome}_{origem})\n"
        #                     pk_create = True

        #             for nome, info in propriedades_destino.items():
        #                 if (info['optional'] == False) and (info['unique'] == True):
        #                     script_sql_pk += f"  CONSTRAINT pk_{origem}_{nome} PRIMARY KEY ({nome}_{origem})\n"
        #                     pk_create = True

        #             if pk_create == False:
        #                 script_sql += primary_key

        #             script_sql += script_sql_pk
        #             script_sql += ");\n\n"

##############################################

    # Gerar os inserts dos relacionamentos
    i = 0
    insert_sql = []

    # Percorrer todos os relacionamentos
    for rel_data in pg_schema_dict["relationships"]:
        cardinality = rel_data.get("cardinality_type", "Unknown")

        if cardinality == "N:N":
            print("N:N")
            rel_name = rel_data["relationship_type"].lower()
            origem = '_'.join(rel_data["origin"]).lower()
            destino = '_'.join(rel_data["destination"]).lower()

            if origem in PALAVRAS_RESERVADAS:
                origem += "_table"
            if destino in PALAVRAS_RESERVADAS:
                destino += "_table"

            rel_table = f"{origem}_{rel_name}_{destino}"

            origem_info = pg_schema_dict["nodes"][rel_data["origin"]]["primary_key_info"]
            destino_info = pg_schema_dict["nodes"][rel_data["destination"]]["primary_key_info"]

            colunas_insert = []

            # Obter colunas relevantes das tabelas origem, destino e relacionamento
            for pk in origem_info:
                if pk["composta"]:
                    name_prop_origem = pk['nome_propriedade'].split(", ")
                    for n in name_prop_origem:
                        colunas_insert.append(f"{origem}_{n}")
                else:
                    if pk['nome_propriedade'] != "id":
                        colunas_insert.append(f"{origem}_{pk['nome_propriedade']}")

            for pk in destino_info:
                if pk["composta"]:
                    name_prop_destino = pk['nome_propriedade'].split(", ")
                    for n in name_prop_destino:
                        colunas_insert.append(f"{destino}_{n}")
                else:
                    if pk['nome_propriedade'] != "id":
                        colunas_insert.append(f"{destino}_{pk['nome_propriedade']}")

            for prop in rel_data["properties"]:
                colunas_insert.append(prop)

            # Processar os valores para cada relacionamento
            for rel in rel_data["valores_insert"]:
                valores_insert = []

                set_clauses = []
                where_clauses = []

                # Adicionar valores das chaves e propriedades do nodo origem
                for pk in origem_info:
                    nome_propriedade = pk["nome_propriedade"]

                    if pk["composta"]:
                        nome_propriedade = nome_propriedade.split(", ")
                        for n in nome_propriedade:
                            valor = rel["propriedades_origem"].get(n)

                            if isinstance(valor, str):
                                valor = valor.replace("'", " ")

                            valores_insert.append(f"'{valor}'" if valor is not None else "NULL")
                    else:
                        if pk['nome_propriedade'] != "id":
                            # print(valor)
                            valor = rel["propriedades_origem"].get(nome_propriedade)

                            if isinstance(valor, str):
                                valor = valor.replace("'", " ")

                            valores_insert.append(f"'{valor}'" if valor is not None else "NULL")

                # Adicionar valores das chaves e propriedades do nodo destino
                for pk in destino_info:
                    nome_propriedade = pk["nome_propriedade"]

                    if pk["composta"]:
                        nome_propriedade = nome_propriedade.split(", ")
                        for n in nome_propriedade:
                            valor = rel["propriedades_destino"].get(n) 

                            if isinstance(valor, str):
                                valor = valor.replace("'", " ")

                            valores_insert.append(f"'{valor}'" if valor is not None else "NULL")
                    else:
                        if pk['nome_propriedade'] != "id":
                            valor = rel["propriedades_destino"].get(nome_propriedade)

                            if isinstance(valor, str):
                                valor = valor.replace("'", " ")

                            valores_insert.append(f"'{valor}'" if valor is not None else "NULL")

                # Adicionar valores das propriedades do relacionamento
                for prop in rel_data["properties"]:
                    valor = rel["propriedades_relacionamento"].get(prop)

                    if isinstance(valor, str):
                        valor = valor.replace("'", " ")

                    valores_insert.append(f"'{valor}'" if valor is not None else "NULL")

                # Criar comando INSERT individual para cada linha de valores
                insert_sql.append(
                    f"INSERT INTO {rel_table} ({', '.join(colunas_insert)}) VALUES ({', '.join(valores_insert)});\n"
                )

            # Verificar a cardinalidade (1:N)
        if cardinality == "1:N":
            print("1:N")
            for rel in rel_data["valores_insert"]:
                # print(rel_data["valores_insert"])
                for pk in origem_info:
                    nome_propriedade = pk["nome_propriedade"]
                    if pk["composta"]:
                        print("A")
                        nome_propriedade = nome_propriedade.split(", ")
                        for n in nome_propriedade:
                            valor_origem = rel["propriedades_origem"].get(n)
                            id_destino = rel["propriedades_destino"].get("id")  # Ajustar conforme chave real
                            if valor_origem is not None and id_destino is not None:
                                insert_sql.append(
                                    f"UPDATE {destino} SET {origem}_{n} = '{valor_origem}' WHERE id = '{id_destino}';\n"
                                )
                    else:
                        # print("B")
                        valor_origem = rel["propriedades_origem"].get(nome_propriedade)
                        id_destino = rel["propriedades_destino"].get("id")  # Ajustar conforme chave real
                        if valor_origem is not None and id_destino is not None:
                            print("C")
                            insert_sql.append(
                                f"UPDATE {destino} SET {origem}_{nome_propriedade} = '{valor_origem}' WHERE id = '{id_destino}';\n"
                            )
            
        # elif cardinality == "N:1":
        #     target_table = origem
        #     for pk in origem_info:
        #         col = pk["nome_propriedade"]
        #         if pk["composta"]:
        #             for n in pk["nome_propriedade"].split(", "):
        #                 val = rel["propriedades_origem"].get(n)
        #                 set_clauses.append(f"{origem}_{n} = '{val}'" if val is not None else f"{origem}_{n} = NULL")
        #         else:
        #             if pk["nome_propriedade"] != "id":
        #                 val = rel["propriedades_origem"].get(col)
        #                 set_clauses.append(f"{origem}_{col} = '{val}'" if val is not None else f"{origem}_{col} = NULL")
        #     for pk in destino_info:
        #         col = pk["nome_propriedade"]
        #         if pk["composta"]:
        #             for n in pk["nome_propriedade"].split(", "):
        #                 val = rel["propriedades_destino"].get(n)
        #                 where_clauses.append(f"{n} = '{val}'" if val is not None else f"{n} IS NULL")
        #         else:
        #             if pk["nome_propriedade"] != "id":
        #                 val = rel["propriedades_destino"].get(col)
        #                 where_clauses.append(f"{col} = '{val}'" if val is not None else f"{col} IS NULL")

        # elif cardinality == "1:1":
        #     if rel_data.get("more_occurrence") == rel_data["origin"]:
        #         target_table = destino
        #         for pk in destino_info:
        #             col = pk["nome_propriedade"]
        #             if pk["composta"]:
        #                 for n in pk["nome_propriedade"].split(", "):
        #                     val = rel["propriedades_destino"].get(n)
        #                     where_clauses.append(f"{n} = '{val}'" if val is not None else f"{n} IS NULL")
        #             else:
        #                 if pk["nome_propriedade"] != "id":
        #                     val = rel["propriedades_destino"].get(col)
        #                     where_clauses.append(f"{col} = '{val}'" if val is not None else f"{col} IS NULL")
        #         for pk in origem_info:
        #             col = pk["nome_propriedade"]
        #             if pk["composta"]:
        #                 for n in pk["nome_propriedade"].split(", "):
        #                     val = rel["propriedades_origem"].get(n)
        #                     set_clauses.append(f"{origem}_{n} = '{val}'" if val is not None else f"{origem}_{n} = NULL")
        #             else:
        #                 if pk["nome_propriedade"] != "id":
        #                     val = rel["propriedades_origem"].get(col)
        #                     set_clauses.append(f"{origem}_{col} = '{val}'" if val is not None else f"{origem}_{col} = NULL")
        #     else:
        #         target_table = origem
        #         for pk in origem_info:
        #             col = pk["nome_propriedade"]
        #             if pk["composta"]:
        #                 for n in pk["nome_propriedade"].split(", "):
        #                     val = rel["propriedades_origem"].get(n)
        #                     where_clauses.append(f"{n} = '{val}'" if val is not None else f"{n} IS NULL")
        #             else:
        #                 if pk["nome_propriedade"] != "id":
        #                     val = rel["propriedades_origem"].get(col)
        #                     where_clauses.append(f"{col} = '{val}'" if val is not None else f"{col} IS NULL")
        #         for pk in destino_info:
        #             col = pk["nome_propriedade"]
        #             if pk["composta"]:
        #                 for n in pk["nome_propriedade"].split(", "):
        #                     val = rel["propriedades_destino"].get(n)
        #                     set_clauses.append(f"{destino}_{n} = '{val}'" if val is not None else f"{destino}_{n} = NULL")
        #             else:
        #                 if pk["nome_propriedade"] != "id":
        #                     val = rel["propriedades_destino"].get(col)
        #                     set_clauses.append(f"{destino}_{col} = '{val}'" if val is not None else f"{destino}_{col} = NULL")

        # else:
        #     # autorelacionamento
        #     target_table = origem
        #     for key, val in rel["propriedades_origem"].items():
        #         set_clauses.append(f"{key} = '{val}'" if val is not None else f"{key} = NULL")
        #     for key, val in rel["propriedades_destino"].items():
        #         where_clauses.append(f"{key} = '{val}'" if val is not None else f"{key} IS NULL")
        
        # update_query = f"UPDATE {target_table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)};"
        # insert_sql.append(update_query)
        # i += 1
        # print(f"Processado relacionamento {i}")

    return script_sql, "".join(insert_sql)