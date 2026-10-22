
import json
import os
import smtplib
import urllib.request
import urllib.error
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
REPORTES = BASE / "reportes"

PORTALES_SEACE = [
    (
        "Buscador público SEACE",
        "https://prod1.seace.gob.pe/"
        "SeaceWeb-PRO/public/"
        "buscarProcedimientosSeleccion.iface?init=1",
    ),
    (
        "Buscador público SEACE alternativo",
        "https://prod2.seace.gob.pe/"
        "seacebus-uiwd-pub/buscadorPublico/"
        "buscadorPublico.xhtml",
    ),
]


def comprobar_portal(url):
    solicitud = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; "
                "PubligrafKeniaBot/1.0)"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
        },
    )

    try:
        with urllib.request.urlopen(
            solicitud, timeout=25
        ) as respuesta:
            codigo = respuesta.status
            respuesta.read(1024)
            return codigo, "Respuesta HTTP recibida"

    except urllib.error.HTTPError as error:
        return error.code, f"El servidor respondió HTTP {error.code}"

    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def revisar_portales():
    resultados = []

    for nombre, url in PORTALES_SEACE:
        codigo, detalle = comprobar_portal(url)
        resultados.append({
            "nombre": nombre,
            "url": url,
            "codigo": codigo,
            "detalle": detalle,
        })

        if codigo == 200:
            break

    return resultados


def enviar_correo(destino, asunto, contenido):
    usuario = os.environ.get("GMAIL_USER")
    clave = os.environ.get("GMAIL_APP_PASSWORD")

    if not usuario or not clave:
        raise RuntimeError(
            "Falta configurar GMAIL_USER o "
            "GMAIL_APP_PASSWORD en GitHub Secrets."
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
        raise FileNotFoundError(
            "No se encuentra config.json"
        )

    with CONFIG.open("r", encoding="utf-8") as archivo:
        config = json.load(archivo)

    zona = ZoneInfo(
        config.get("timezone", "America/Lima")
    )
    ahora = datetime.now(zona)
    REPORTES.mkdir(parents=True, exist_ok=True)

    resultados = revisar_portales()
    accesible = any(
        resultado["codigo"] == 200
        for resultado in resultados
    )

    lineas = [
        "# Bot de licitaciones - Publigraf Kenia",
        "",
        f"Fecha: {ahora:%d/%m/%Y %H:%M:%S}",
        "",
        "## Estado de la consulta",
        (
            "- Acceso HTTP a un portal público: "
            + ("RESPUESTA 200" if accesible else "NO CONFIRMADO")
        ),
        "- Búsqueda real de convocatorias: "
        "PENDIENTE DE IMPLEMENTAR",
        "- Convocatorias verificadas: ninguna",
        "",
        "## Comprobación de portales",
    ]

    for resultado in resultados:
        codigo = resultado["codigo"]
        estado = (
            str(codigo) if codigo is not None
            else "SIN RESPUESTA"
        )
        lineas.extend([
            "",
            f"### {resultado['nombre']}",
            f"- Código HTTP: {estado}",
            f"- Detalle: {resultado['detalle']}",
            f"- Dirección: {resultado['url']}",
        ])

    lineas.extend([
        "",
        "## Categorías configuradas",
    ])

    for categoria in config.get("categories", []):
        nombre = categoria.get("name", "Sin nombre")
        palabras = categoria.get("keywords", [])
        lineas.append(
            f"- {nombre}: "
            f"{', '.join(palabras) or 'sin palabras clave'}"
        )

    lineas.extend([
        "",
        "## Importante",
        "Una respuesta HTTP 200 solo confirma que el servidor "
        "respondió. No confirma que se hayan buscado ni "
        "encontrado convocatorias.",
        "",
        "El buscador automático y la validación de oportunidades "
        "siguen pendientes.",
    ])

    contenido = "\n".join(lineas) + "\n"
    ruta = REPORTES / (
        f"informe-{ahora:%Y%m%d-%H%M%S}.md"
    )
    ruta.write_text(contenido, encoding="utf-8")

    print(f"Informe creado: {ruta}")
    print(
        "Portal accesible:",
        "sí" if accesible else "no confirmado",
    )

    if config.get("send_email", False):
        destino = config.get("email_to")

        if not destino:
            raise RuntimeError(
                "Falta email_to en config.json"
            )

        enviar_correo(
            destino,
            f"Informe del bot Publigraf Kenia - "
            f"{ahora:%d/%m/%Y}",
            contenido,
        )
        print(f"Correo enviado a {destino}")
    else:
        print("Envío desactivado en config.json")


if __name__ == "__main__":
    main()
