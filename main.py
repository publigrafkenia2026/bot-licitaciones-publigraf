"""
Bot inicial de licitaciones para Publigraf Kenia.
Esta primera versión NO afirma que haya encontrado todas las convocatorias:
deja lista la estructura para conectar fuentes oficiales verificadas.
"""
import json
import os
from datetime import datetime
from pathlib import Path

KEYWORDS_FILE = Path("config.json")
OUTPUT_DIR = Path("informes")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_config():
    with KEYWORDS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    config = load_config()
    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    report = [
        "# Informe inicial de monitoreo de licitaciones",
        "",
        f"Generado: {now}",
        "",
        "## Categorías configuradas",
    ]
    for category in config["categories"]:
        report.append(f"- **{category['name']}**: {', '.join(category['keywords'])}")
    report += [
        "",
        "## Estado",
        "",
        "Esta versión inicial solo valida la configuración y genera este informe.",
        "Aún no consulta fuentes de contratación, no descarga PDF y no envía correos.",
        "Esas funciones se agregarán después de verificar las fuentes oficiales y configurar",
        "las credenciales de forma segura mediante GitHub Secrets.",
        "",
        "No uses este informe como lista de oportunidades reales.",
    ]
    output = OUTPUT_DIR / "informe_inicial.md"
    output.write_text("\n".join(report), encoding="utf-8")
    print(f"Informe creado: {output}")

if __name__ == "__main__":
    main()
