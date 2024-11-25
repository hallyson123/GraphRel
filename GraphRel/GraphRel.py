import pickle

ARRAY_LIST = True
DUAS_TABELAS_CASO_DOIS = False
LISTA_COMO_TABELA = True

def modificar_tipos(tipo, prop_data):
    if tipo == "str":
        tipo = f"VARCHAR({prop_data['tamStr']})" if prop_data["tamStr"] >= 100 else "VARCHAR(100)"
    if tipo == "int":
        tipo = "integer"
    if tipo == "float":
        tipo = "real"

    if prop_data["is_enum"]:
        tipo = prop_data["typeEnum"]

    if prop_data["unique"]:
        tipo += " UNIQUE"
    if not prop_data["optional"]:
        tipo += " NOT NULL"

    return tipo

# gerar o script SQL
def gerar_script_sql(pg_schema_dict):
    script_sql = ""
    aux_sql_list = ""

    script_sql += "CREATE DATABASE TesteRel; \n"
    script_sql += "\c TesteRel\n"

    # Criar tipo ENUM (nodos)
    for node_name, node_data in pg_schema_dict["nodes"].items():
        for prop, prop_data in node_data["properties"].items():
            if prop_data["is_enum"]:
                node = ''.join(node_name)
                tipo_enum = f"{node}_{prop}_enum"
                prop_data["typeEnum"] = tipo_enum
                script_sql += f"CREATE TYPE {tipo_enum.upper()} AS ENUM({prop_data['values']})\n"

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
                script_sql += f"CREATE TYPE {tipo_enum.upper()} AS ENUM({prop_data['valores_enum']})\n"

    script_sql += "\n"

    # Criar tabelas para os nodos
    script_sql += "/*Criando tabelas com atributos, tipos e PK*/\n"

    nodos_com_um_rotulo = []
    nodos_com_multiplos_rotulos = []

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

        script_sql += f"CREATE TABLE {tabela_nome} (\n"
        primary_key_set = False

        if not node_data["uniqueProperties"]:
            script_sql += "  id SERIAL PRIMARY KEY,\n"
            node_data["primary_key_info"] = [{"nome_propriedade": "id", "nome_chave": "id", "tipo_propriedade": "INTEGER", "composta": False}]
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
                    tipo = f"VARCHAR(100)" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
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
            if len(node_data["uniqueProperties"]) == 1:
                prop_primary = node_data["uniqueProperties"][0]
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({prop_primary}) \n"
                
                node_data["primary_key_info"].append({"nome_propriedade": prop_primary, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": False})
                # print(node_data["primary_key_info"])
            
            else:
                chave_composta = node_data["uniqueProperties"]
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({chave_composta}), \n"

                node_data["primary_key_info"].append({"nome_propriedade": chave_composta, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True})
                print(node_data["primary_key_info"])

            primary_key_set = True

        script_sql = script_sql.rstrip(",\n")
        script_sql += "\n);\n\n"

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
    script_sql += aux_sql_list

    # Criar tabelas para nodos com **mais de um** rótulo
    for node_name, node_data in nodos_com_multiplos_rotulos:
        node = '_'.join(node_name)
        tabela_nome = node.lower()

        tipo_enum_filhos = f"{tabela_nome}_tipo_enum"
        script_sql += f"CREATE TYPE {tipo_enum_filhos.upper()} AS ENUM({', '.join([f'\'{child_label}\'' for child_label in node_name])})\n\n"

        script_sql += f"CREATE TABLE {tabela_nome} (\n"
        primary_key_set = False

        if not node_data["uniqueProperties"]:
            script_sql += "  id SERIAL PRIMARY KEY,\n"
            node_data["primary_key_info"] = [{"nome_propriedade": "id", "nome_chave": "id", "tipo_propriedade": "INTEGER", "composta": False}]
            primary_key_set = True

        script_sql += f"  tipo {tipo_enum_filhos.upper()},\n"

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
                    tipo = f"VARCHAR(100)" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
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
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({prop_primary}) \n"
                
                node_data["primary_key_info"].append({"nome_propriedade": prop_primary, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": False})
            
            else:
                chave_composta = node_data["uniqueProperties"]
                script_sql += f"  CONSTRAINT pk_{node.lower()} PRIMARY KEY ({chave_composta}), \n"

                node_data["primary_key_info"].append({"nome_propriedade": chave_composta, "nome_chave": f"{tabela_nome}", "tipo_propriedade": tipo_fk, "composta": True})

            primary_key_set = True

        script_sql = script_sql.rstrip(",\n")
        script_sql += "\n);\n\n"

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

####################################################################################################

    script_sql += "/*Inicio de tratamento de relacionamentos:*/\n"
    # Adicionar relacionamentos
    for rel in pg_schema_dict["relationships"]:
        rel_name = rel["relationship_type"].lower()
        origem = '_'.join(rel["origin"]).lower()
        destino = '_'.join(rel["destination"]).lower()

        # print(pg_schema_dict["relationships"])

        origem_info = pg_schema_dict["nodes"][rel["origin"]]["primary_key_info"]
        destino_info = pg_schema_dict["nodes"][rel["destination"]]["primary_key_info"] #VERIFICAR PQ N APARECE O DESTINO

        # Interpreta a cardinalidade para definir as constraints
        # origem_card, destino_card = rel["cardinality"].split(';')
        destino_card, origem_card = rel["cardinality"].split(';')
        origem_min, origem_max = origem_card[1:-1].split(':')
        destino_min, destino_max = destino_card[1:-1].split(':')

        rel_table = f"{origem.upper()}_{rel_name}_{destino.upper()}"

        # Propriedades do relacionamentos
        properties_rel = ""
        for prop, prop_data in rel["properties"].items():
            if prop_data["is_enum"]:
                print(prop_data)
                tipo = f"{prop_data['typeEnum']}"
            else:
                if prop_data["is_list"]:
                    tipo = prop_data['list_info']['tipo_item']
                    tipo = tipo = f"VARCHAR(100)" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    tipo += '[]'
                else:
                    tipo = ','.join(prop_data["tipos"])
                    tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
            # Adicionar constraints de unicidade ou obrigatoriedade
            if prop_data.get("is_singleton"):
                tipo += " UNIQUE"
            if prop_data.get("is_mandatory"):
                tipo += f" NOT NULL"
            
            properties_rel += f"  {prop} {tipo.upper()},\n"

        # MUITOS PARA MUITOS (N:N)
        if origem_max == "N" and destino_max == "N" and origem != destino:
            # print("N:N")
            script_sql += "/*Criacao de rel (N:N)*/\n"
            script_sql += f"CREATE TABLE {rel_table} (\n"

            foreign_keys = ""

            # Chaves estrangeiras para origem e destino (criar colunas)
            for pk in origem_info:
                nome_propriedade = pk['nome_propriedade']
                if pk['composta']:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][nome]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome}) REFERENCES {origem}({nome}),\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"  {origem}_id {pk['tipo_propriedade']},\n"
                        foreign_keys += f"  FOREIGN KEY ({origem}_{nome_propriedade}) REFERENCES {origem}({pk['nome_propriedade']}),\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][pk['nome_propriedade']]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome_propriedade} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome_propriedade}) REFERENCES {origem}({pk['nome_propriedade']}),\n"

            for pk in destino_info:
                nome_propriedade = pk['nome_propriedade']
                if pk['composta']:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][nome]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome}) REFERENCES {destino}({nome}),\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"  {destino}_id {pk['tipo_propriedade']},\n"
                        foreign_keys += f"  FOREIGN KEY ({destino}_{nome_propriedade}) REFERENCES {destino}({pk['nome_propriedade']}),\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][pk['nome_propriedade']]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {pk['nome_chave']}_{nome_propriedade} {tipo.upper()},\n"
                        foreign_keys += f"  FOREIGN KEY ({pk['nome_chave']}_{nome_propriedade}) REFERENCES {destino}({pk['nome_propriedade']}),\n"

            script_sql += properties_rel.rstrip(",\n")
            script_sql += ",\n"
            script_sql += foreign_keys.rstrip(",\n")
            script_sql += "\n);\n"

            script_sql += "/*Criacao de rel (N:N) finalizada*/\n\n"

####################################################################################################

        # TRATAR AUTORELACIONAMENTO
        elif origem == destino:
            script_sql += "/*Criacao de Autorelacionamento*/\n"
            # print("AUTO")
            for pk in origem_info:
                nome_propriedade = pk['nome_propriedade']
                if pk['composta']:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin_{nome} {tipo},\n"
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination_{nome} {tipo},\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({nome}),\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({nome});\n\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin INTEGER,\n"
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination INTEGER,\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({pk['nome_propriedade']}),\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({pk['nome_propriedade']});\n\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel['origin']]['properties'][pk['nome_propriedade']]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_origin {tipo},\n"
                        script_sql += f"ALTER TABLE {origem} ADD COLUMN {origem}_{rel_name}_destination {tipo},\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_origin) REFERENCES {origem}({nome_propriedade}),\n"
                        script_sql += f"FOREIGN KEY ({origem}_{rel_name}_destination) REFERENCES {origem}({nome_propriedade});\n\n"

            script_sql += "/*Criacao de Autorelacionamento finalizado*/\n\n"

####################################################################################################

        elif origem_max == "N" and destino_max == "1":  # 1:N
            # print("1:N")
            script_sql += "/*Criacao de rel (1:N)*/\n"
            for pk in origem_info:
                nome_propriedade = pk['nome_propriedade']
                if pk["composta"]:
                    for nome in nome_propriedade:
                        tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_{nome} {tipo},\n"
                        script_sql += f"FOREIGN KEY ({origem}_{nome}) REFERENCES {origem}({nome});\n\n"
                else:
                    if pk['nome_propriedade'] == 'id':
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_id INTEGER,\n"
                        script_sql += f"FOREIGN KEY ({origem}_id) REFERENCES {origem}(id);\n\n"
                    else:
                        tipo = pg_schema_dict["nodes"][rel["origin"]]['properties'][nome_propriedade]['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"ALTER TABLE {destino} ADD COLUMN {origem}_{nome_propriedade} {tipo},\n"
                        script_sql += f"FOREIGN KEY ({origem}_{nome_propriedade}) REFERENCES {origem}({nome_propriedade});\n\n"
            
            script_sql += "/*Finalizado criacao de rel (1:N)*/\n\n"

        elif origem_max == "1" and destino_max == "N":  # N:1
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
                    tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_{nome} {tipo},\n"
                    script_sql += f"FOREIGN KEY ({destino}_{nome}) REFERENCES {destino}({nome});\n\n"
            else:
                if pk_destino['nome_propriedade'] == 'id':
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_id INTEGER,\n"
                    script_sql += f"FOREIGN KEY ({destino}_id) REFERENCES {destino}(id);\n\n"
                else:
                    tipo = pg_schema_dict["nodes"][rel["destination"]]['properties'][nome_propriedade_destino]['type']
                    tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                    script_sql += f"ALTER TABLE {origem} ADD COLUMN {destino}_{nome_propriedade_destino} {tipo},\n"
                    script_sql += f"FOREIGN KEY ({destino}_{nome_propriedade_destino}) REFERENCES {destino}({nome_propriedade_destino});\n\n"
    
            script_sql += "/*Criacao de rel (N:1) finalizado*/\n\n"

####################################################################################################

        elif origem_max == "1" and destino_max == "1":
            if DUAS_TABELAS_CASO_DOIS and rel['more_occurrence'] != None:
                # Caso 2: Baixa ocorrência. Um dos rótulos tem mais ocorrência que o outro.
                # Cria-se duas tabelas, aquela que representa o rótulo com menor ocorrência recebe a chave do maior.

                # print('(1:1) DUAS TABELA')
                
                rotulo_mais_ocorrencia = tuple(rel['more_occurrence'])
                origem_key = tuple(rel["origin"])
                destino_key = tuple(rel["destination"])
                propriedades_origem = pg_schema_dict["nodes"][origem_key]['properties']
                propriedades_destino = pg_schema_dict["nodes"][destino_key]['properties']

                # print(origem_key, destino_key, rotulo_mais_ocorrencia)

                # Definindo qual é o lado com maior ocorrência e qual é o lado com menor ocorrência
                if rotulo_mais_ocorrencia == origem_key:
                    tabela_principal = origem
                    tabela_dependente = destino
                    propriedades_principal = propriedades_origem
                    propriedades_dependente = propriedades_destino
                else:
                    tabela_principal = destino
                    tabela_dependente = origem
                    propriedades_principal = propriedades_destino
                    propriedades_dependente = propriedades_origem

                # Criando a tabela para o lado principal
                script_sql += f"CREATE TABLE {tabela_principal} (\n"
                for nome, info in propriedades_principal.items():
                    script_sql += f"  {nome} {info['type'].upper()}"
                    
                    if info['unique']:
                        script_sql += " UNIQUE"
                    if info['optional'] == False:
                        script_sql += " NOT NULL"
                    script_sql += ",\n"
                
                # Definindo a chave primária do lado principal
                script_sql += "  id SERIAL PRIMARY KEY\n"
                script_sql += ");\n\n"

                # Criando a tabela para o lado dependente com chave estrangeira referenciando o principal
                script_sql += f"CREATE TABLE {tabela_dependente} (\n"
                for nome, info in propriedades_dependente.items():
                    script_sql += f"  {nome} {info['type'].upper()}"
                    
                    if info['unique']:
                        script_sql += " UNIQUE"
                    if info['optional'] == False:
                        script_sql += " NOT NULL"
                    script_sql += ",\n"
                
                # Adicionando chave estrangeira no lado dependente
                script_sql += f"  {tabela_principal}_id INTEGER REFERENCES {tabela_principal}(id)\n"
                script_sql += ");\n\n"

            else:
                # Caso 1: Alta ocorrência, criar tabela unificada
                if rel["merge"]:
                    # print('(1:1) UNIFICAR TABELAS')
                    script_sql += "/*Criacao de rel (1:1) (Unificar nodos)*/\n"
                    origem_key = tuple(rel["origin"])
                    destino_key = tuple(rel["destination"])
                    propriedades_origem = pg_schema_dict["nodes"][origem_key]['properties']
                    propriedades_destino = pg_schema_dict["nodes"][destino_key]['properties']
                    # print(propriedades_origem)
                    # print(propriedades_destino)

                    # Define o nome da tabela: com com mais propriedades é a principal, se for igual escolhe uma (origem)
                    if len(pg_schema_dict["nodes"][origem_key]['properties']) >= len(pg_schema_dict["nodes"][destino_key]['properties']):
                        table_name = origem
                    else:
                        table_name = destino

                    script_sql += f"CREATE TABLE {table_name}_unificada (\n"
                    
                    # Adiciona colunas da tabela de origem
                    for nome, info in propriedades_origem.items():
                        tipo = info['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {nome}_{origem} {tipo.upper()}"

                        if info['unique']:
                            script_sql += " UNIQUE"

                        if info['optional'] == False:
                            script_sql += " NOT NULL,\n"

                    # Adiciona colunas da tabela de destino
                    for nome, info in propriedades_destino.items():
                        tipo = info['type']
                        tipo = f"VARCHAR({prop_data.get('tamStr', 100)})" if tipo == "str" else ("INTEGER" if tipo == "int" else "REAL")
                        script_sql += f"  {nome}_{destino} {tipo.upper()}"

                        if info['unique']:
                            script_sql += " UNIQUE"
                            
                        if info['optional'] == False:
                            script_sql += " NOT NULL,\n"
                    
                    # # Define a chave primária origem
                    pk_create = False
                    primary_key = "  id SERIAL PRIMARY KEY, "
                    script_sql_pk = ""

                    for nome, info in propriedades_origem.items():
                        if (info['optional'] == False) and (info['unique'] == True):
                            script_sql_pk += f"  CONSTRAINT pk_{origem}_{nome} PRIMARY KEY ({nome}_{origem})\n"
                            pk_create = True

                    for nome, info in propriedades_destino.items():
                        if (info['optional'] == False) and (info['unique'] == True):
                            script_sql_pk += f"  CONSTRAINT pk_{origem}_{nome} PRIMARY KEY ({nome}_{origem})\n"
                            pk_create = True

                    if pk_create == False:
                        script_sql += primary_key

                    script_sql += script_sql_pk
                    script_sql += ");\n\n"

    return script_sql

# Carregar o dicionário
file_path = "GraphRel/nos_dump.pkl"
# file_path = "GraphRel/airbnb.pkl"
# file_path = "GraphRel/movie.pkl"

with open(file_path, "rb") as f:
    pg_schema_dict = pickle.load(f)

# Gerar o script SQL
script_sql = gerar_script_sql(pg_schema_dict)

# Salvar o script em um arquivo SQL
with open("GraphRel/graph_to_rel.sql", "w") as f:
    f.write(script_sql)

print("Script SQL gerado com sucesso: graph_to_rel.sql")
