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