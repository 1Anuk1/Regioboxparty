# regioweb/utils.py

import hashlib, time

# Generar token único y temporal
def generar_token(cliente):
    timestamp = int(time.time())
    value = f"{cliente.idCliente}-{timestamp}-{cliente.contraseña}"
    token = hashlib.sha256(value.encode()).hexdigest()
    return f"{token}-{timestamp}"

# Validar token, caduca en 1 hora (3600s)
def validar_token(cliente, token):
    try:
        hash_val, timestamp = token.split("-")
        timestamp = int(timestamp)
        if time.time() - timestamp > 3600:
            return False
        expected = hashlib.sha256(f"{cliente.idCliente}-{timestamp}-{cliente.contraseña}".encode()).hexdigest()
        return expected == hash_val
    except:
        return False
