
import json
import os
import smtplib
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
REPORTES = BASE / "reportes"

SEACE_URL = (
    "https://prod2.seace.gob.pe/"
    "seacebus-uiwd-pub/buscadorPublico/"
    "buscadorPublico.xhtml"
)


def comprobar_seace():
    """Comprueba el acceso al portal; no simula resultados."""
    solicitud = urllib.request.Request(
        SEACE_URL,
        headers={"User-Agent": "PubligrafKeniaBot/1.0"},
    )

    try:
        with urllib.request.urlopen(
            solicitud, timeout=30
        ) as respuesta:
            estado = respuesta.status
            contenido = respuesta.read(500_000).decode(
                "utf-8", errors="replace"
            )

        if estado == 200:
            return (
                "ACCESIBLE",
                f"El portal oficial respondió HTTP {estado}. "
                "Esto no significa que se hayan consultado "
                "convocatorias ni obtenido resultados.",
            )

        return (
            "NO VERIFICADO",
            f"El portal respondió HTTP {estado}.",
        )

    except Exception as error:
        return (
            "ERROR",
            f"No se pudo consultar el portal: {error}",
        )


def enviar_correo(destino, asunto, contenido):
    usuario = os.environ.get("GMAIL_USER")
    clave = os.environ.get("GMAIL_APP_PASSWORD")

    if not usuario or not clave:
        raise RuntimeError(
            "Faltan los secretos GMAIL_USER o "
            "GMAIL_APP_PASSWORD en GitHub Actions."
        )

    mensaje = EmailMessage()
    mensaje["From"] = usuario
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(contenido)

    with smtplib.SMTP(
        "smtp.gmail.com", 587, timeout=30
    ) as servidor:
        servidor.starttls()
        servidor.login(usuario, clave)
        servidor.send_message(mensaje)


def main():
    if not CONFIG.exists():
        raise FileNotFoundError("No se encuentra config.json")

    with CONFIG.open("r", encoding="utf-8") as archivo:
        config = json.load(archivo)

    zona = ZoneInfo(
        config.get("timezone", "America/Lima")
    )
    ahora = datetime.now(zona)
    REPORTES.mkdir(parents=True, exist_ok=True)

    estado, detalle = comprobar_seace()

    lineas = [
        "# Bot de licitaciones - Publigraf Kenia",
        "",
        f"Fecha: {ahora:%d/%m/%Y %H:%M:%S}",
        "",
        "## Resultado de la ejecución",
        "- Programa ejecutado: sí",
        f"- Acceso al portal SEACE: {estado}",
        f"- Detalle: {detalle}",
        "- Búsqueda automatizada de convocatorias: "
        "PENDIENTE DE IMPLEMENTAR",
        "- Resultados reales verificados: ninguno",
        "",
        "## Categorías de interés",
    ]

    for categoria in config.get("categories", []):
        nombre = categoria.get("name", "Sin nombre")
        palabras = categoria.get("keywords", [])
        lineas.append(
            f"- {nombre}: "
            f"{', '.join(palabras) or 'sin palabras clave'}"
        )

    lineas.extend([
        "",
        "## Portal oficial",
        SEACE_URL,
        "",
        "AVISO: comprobar el acceso al portal no equivale "
        "a buscar ni validar oportunidades de contratación.",
    ])

    contenido = "\n".join(lineas) + "\n"
    archivo_salida = REPORTES / (
        f"informe-{ahora:%Y%m%d-%H%M%S}.md"
    )
    archivo_salida.write_text(
        contenido, encoding="utf-8"
    )

    print(f"Informe creado: {archivo_salida}")
    print(f"Acceso SEACE: {estado}")

    if config.get("send_email", False):
        destino = config.get("email_to")
        if not destino:
            raise RuntimeError(
                "Falta email_to en config.json"
            )

        enviar_correo(
            destino,
            f"Estado del bot Publigraf Kenia - "
            f"{ahora:%d/%m/%Y}",
            contenido,
        )
        print(f"Correo enviado a {destino}")
    else:
        print("Envío desactivado en config.json")


if __name__ == "__main__":
    main()
