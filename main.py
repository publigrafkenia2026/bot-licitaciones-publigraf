
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
REPORTES = BASE / "reportes"


def main():
    if not CONFIG.exists():
        raise FileNotFoundError("No se encuentra config.json")

    with CONFIG.open("r", encoding="utf-8") as archivo:
        config = json.load(archivo)

    ahora = datetime.now(
        ZoneInfo(config.get("timezone", "America/Lima"))
    )

    REPORTES.mkdir(parents=True, exist_ok=True)

    lineas = [
        "# Bot de licitaciones Publigraf Kenia",
        "",
        f"Fecha de prueba: {ahora:%d/%m/%Y %H:%M:%S}",
        "Zona horaria: America/Lima",
        "",
        "## Estado",
        "- Ejecución del programa: correcta",
        "- Búsqueda real en SEACE/OECE: pendiente de implementar",
        "- Descarga de documentos PDF: pendiente de implementar",
        "- Envío de correo: pendiente de implementar",
        "",
        "## Categorías configuradas",
    ]

    for categoria in config.get("categories", []):
        nombre = categoria.get("name", "Sin nombre")
        palabras = categoria.get("keywords", [])
        lineas.append(f"- **{nombre}**: {', '.join(palabras) or 'sin palabras clave'}")

    lineas += [
        "",
        "Este informe confirma únicamente la prueba técnica.",
    ]

    destino = REPORTES / f"informe-{ahora:%Y%m%d-%H%M%S}.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print(f"Informe creado correctamente: {destino}")


if __name__ == "__main__":
    main()
