import os
import re

views_dir = r"C:\Users\HP\Dropbox\D+ARQ\2_FINANZAS_Y_CRIPTO\FINANZAS Y CRIPTO\01_SISTEMAS_TRADING\Sistema de opciones\frontend_v4\src\views"

mock_patterns = [
    r'1000557',
    r'144391',
    r'581',
    r'4000000',
    r'17\.0',
    r'3,980',
    r'3,770',
    r'259\.83',
    r'272\.72',
    r'181\.81'
]

print("=== AUDITORÍA DE VISTAS FRONTEND (BÚSQUEDA DE VALORES FALSOS / MOCKS) ===")

for root, dirs, files in os.walk(views_dir):
    for f in files:
        if f.endswith('.tsx') or f.endswith('.ts'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
                for pat in mock_patterns:
                    matches = re.findall(pat, content)
                    if matches:
                        print(f"[FOUND] Coincidencia '{pat}' encontrada en: {f} (Cantidad: {len(matches)})")

print("=== FIN DE AUDITORÍA DE MOCKS ===")
