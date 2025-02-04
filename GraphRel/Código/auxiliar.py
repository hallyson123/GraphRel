def modificar_tipos(tipo, prop_data):
    if tipo == "str":
        tipo = f"VARCHAR"
    if tipo == "int":
        # tipo = "integer"
        tipo = "bigint"
    if tipo == "float":
        tipo = "real"

    if prop_data["is_enum"]:
        tipo = prop_data["typeEnum"]

    if prop_data["unique"]:
        tipo += " UNIQUE"
    if not prop_data["optional"]:
        tipo += " NOT NULL"

    return tipo