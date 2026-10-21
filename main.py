
import json
import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
REPORTES = BASE / "reportes"


def enviar_correo(destino, asunto, contenido):
    usuario = os.environ.get("GMAIL_USER")
    clave = os.environ.get("GMAIL_APP_PASSWORD")

    if not usuario or not clave:
        raise RuntimeError(
            "Faltan los secretos GMAIL_USER o GMAIL_APP_PASSWORD "
            "en GitHub Actions."
        )

    mensaje = EmailMessage()
    mensaje["From"] = usuario
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(contenido)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as servidor:
        servidor.starttls()
        servidor.login(usuario, clave)
        servidor.send_message(mensaje)


def main():
    if not CONFIG.exists():
        raise FileNotFoundError("No se encuentra config.json")

    with CONFIG.open("r", encoding="utf-8") as archivo:
        config = json.load(archivo)

    zona = ZoneInfo(config.get("timezone", "America/Lima"))
    ahora = datetime.now(zona)
    REPORTES.mkdir(parents=True, exist_ok=True)

    lineas = [
        "# Bot de licitaciones Publigraf Kenia",
        "",
        f"Fecha: {ahora:%d/%m/%Y %H:%M:%S}",
        "",
        "## Estado del proyecto",
        "- Ejecución del programa: correcta",
        "- Búsqueda real de licitaciones: pendiente",
        "- Filtrado de convocatorias reales: pendiente",
        "- Envío de correo: configurado por variables seguras",
        "",
        "Este es un informe de prueba técnica. "
        "Todavía no contiene resultados reales de SEACE/OECE.",
        "",
        "## Categorías configuradas",
    ]

    for categoria in config.get("categories", []):
        nombre = categoria.get("name", "Sin nombre")
        palabras = categoria.get("keywords", [])
        lineas.append(
            f"- {nombre}: {', '.join(palabras) or 'sin palabras clave'}"
        )

    contenido = "\n".join(lineas) + "\n"
    destino_archivo = REPORTES / f"informe-{ahora:%Y%m%d-%H%M%S}.md"
    destino_archivo.write_text(contenido, encoding="utf-8")
    print(f"Informe creado: {destino_archivo}")

    if config.get("send_email", False):
        destinatario = config.get("email_to")
        if not destinatario:
            raise RuntimeError("Falta email_to en config.json")

        enviar_correo(
            destinatario,
            f"Prueba del bot Publigraf Kenia - {ahora:%d/%m/%Y}",
            contenido,
        )
        print(f"Correo enviado a {destinatario}")
    else:
        print("Envío desactivado en config.json")


if __name__ == "__main__":
    main()
