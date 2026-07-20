"""Script de ejemplo utilizado como archivo de prueba."""

def backup(origen, destino):
    print(f"Respaldando {origen} en {destino}")

if __name__ == "__main__":
    backup("datos/", "backup/")
