# hash_pass.py
import bcrypt
import getpass # Para ocultar la contraseña mientras escribes

print("--- Generador de Hash Bcrypt ---")

# getpass() oculta la contraseña por seguridad
password = getpass.getpass("Escribe la contraseña para el nuevo usuario: ")

# Hashear la contraseña
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

print("\n¡Hash generado! Cópialo y pégalo en pgAdmin.")
print("--------------------------------------------------")
# Imprimimos el hash decodificado, listo para copiar
print(hashed.decode('utf-8'))
print("--------------------------------------------------")