import re

def validar_nombre(nombre):
    if not nombre:
        raise ValueError("El nombre no puede estar vacío.")
    if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
        raise ValueError("El nombre solo puede contener letras y espacios.")    
    return True, ""
def is_valid_input(data, is_float = False):     
    if data is None:
        return None
    try:
        if is_float:
            return float(data)
        else:
            return int(data)
    except (ValueError, TypeError):
        return None

