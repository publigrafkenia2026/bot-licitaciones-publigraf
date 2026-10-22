
import json
import os
import re
import smtplib
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
REPORTES = BASE / "reportes"
NOTIFICADOS = BASE / "data" / "notificados.json"

API = (
    "https://prod6.seace.gob.pe/v1/s8uit-services/"
    "buscadorpublico/contrataciones/buscador"
)
BUSCADOR = "https://prod6.seace.gob.pe/buscador-publico/"
ZONA = ZoneInfo("America/Lima")
PAGE_SIZE = 100
MAX_PAGES = 50


def normalizar(texto):
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def fecha_seace(texto):
    if not texto:
        return None
    try:
        return datetime.strptime(
            texto, "%d/%m/%Y %H:%M:%S"
        ).replace(tzinfo=ZONA)
    except (ValueError, TypeError):
        return None


def consultar(anio, objeto):
    filas = []
    for pagina in range(1, MAX_PAGES + 1):
        parametros = {
            "anio": str(anio),
            "lista_estado_contrato": "2",
            "lista_codigo_objeto": str(objeto),
            "page": str(pagina),
            "page_size": str(PAGE_SIZE),
        }
        url = API + "?" + urllib.parse.urlencode(parametros)
        solicitud = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 PubligrafKeniaBot/1.0",
            },
        )
        with urllib.request.urlopen(solicitud, timeout=40) as respuesta:
            datos = json.loads(respuesta.read().decode("utf-8"))

        pagina_datos = datos.get("data", [])
        filas.extend(pagina_datos)

        pagina_info = datos.get("pageable", {})
        total = int(pagina_info.get("totalElements", len(filas)))

        if not pagina_datos or pagina * PAGE_SIZE >= total:
            break

    return filas


def buscar_oportunidades(config, ahora):
    categorias = config.get("categories", [])
    palabras = []
    for categoria in categorias:
        palabras.extend(categoria.get("keywords", []))
    palabras = list(dict.fromkeys(
        normalizar(p) for p in palabras if str(p).strip()
    ))

    encontrados = {}
    errores = []

    # 1 = Bien; 2 = Servicio, según el servicio consultado.
    for objeto in (1, 2):
        try:
            filas = consultar(ahora.year, objeto)
            print(f"Objeto {objeto}: {len(filas)} registros recibidos")
        except Exception as error:
            errores.append(f"Objeto {objeto}: {type(error).__name__}: {error}")
            continue

        for fila in filas:
            estado = normalizar(fila.get("nomEstadoContrato", ""))
            if estado != "vigente":
                continue

            limite = fecha_seace(fila.get("fecFinCotizacion"))
            if not limite or limite < ahora:
                continue

            descripcion = str(fila.get("desObjetoContrato", "")).strip()
            numero = str(fila.get("desContratacion", "")).strip()
            entidad = str(fila.get("nomEntidad", "")).strip()
            texto = normalizar(descripcion + " " + numero + " " + entidad)

            coincidencias = [p for p in palabras if p in texto]
            if not coincidencias:
                continue

            identificador = str(fila.get("idContrato", numero))
            encontrados[identificador] = {
                "id": identificador,
                "numero": numero or identificador,
                "entidad": entidad or "Entidad no indicada",
                "descripcion": descripcion or "Descripción no disponible",
                "limite": limite.strftime("%d/%m/%Y %H:%M"),
                "palabras": ", ".join(coincidencias),
                "url": BUSCADOR,
            }

    if not encontrados and errores:
        raise RuntimeError(
            "No se pudo consultar ninguna fuente de datos. "
            + " | ".join(errores)
        )

    return list(encontrados.values()), errores


def cargar_notificados():
    try:
        return json.loads(NOTIFICADOS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def guardar_notificados(ids):
    NOTIFICADOS.parent.mkdir(parents=True, exist_ok=True)
    NOTIFICADOS.write_text(
        json.dumps(sorted(set(ids)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def enviar_correo(destino, asunto, contenido):
    usuario = os.environ.get("GMAIL_USER")
    clave = os.environ.get("GMAIL_APP_PASSWORD")
    if not usuario or not clave:
        raise RuntimeError("Faltan GMAIL_USER o GMAIL_APP_PASSWORD en GitHub Secrets.")

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

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    ahora = datetime.now(ZONA)
    REPORTES.mkdir(parents=True, exist_ok=True)

    oportunidades, errores = buscar_oportunidades(config, ahora)
    anteriores = set(cargar_notificados())
    nuevas = [o for o in oportunidades if o["id"] not in anteriores]

    lineas = [
        "# Alertas de contratos menores — Publigraf Kenia",
        "",
        f"Fecha de consulta: {ahora:%d/%m/%Y %H:%M:%S} (Perú)",
        f"Coincidencias vigentes encontradas: {len(oportunidades)}",
        f"Nuevas coincidencias para notificar: {len(nuevas)}",
        "",
    ]

    if errores:
        lineas.extend(["## Avisos de consulta", *[f"- {e}" for e in errores], ""])

    if nuevas:
        lineas.append("## Nuevas oportunidades")
        for o in nuevas:
            lineas.extend([
                "",
                f"### {o['numero']}",
                f"- Entidad: {o['entidad']}",
                f"- Descripción: {o['descripcion']}",
                f"- Límite de cotización: {o['limite']}",
                f"- Palabras coincidentes: {o['palabras']}",
                f"- Abrir buscador oficial: {o['url']}",
                f"- Buscar el código en el portal: {o['numero']}",
            ])
    else:
        lineas.extend([
            "No se encontraron coincidencias nuevas para notificar.",
            "Esto no significa necesariamente que no existan otras contrataciones.",
        ])

    lineas.extend([
        "",
        "Verifica el estado, los documentos y la fecha límite en el portal oficial antes de cotizar.",
        BUSCADOR,
    ])
    contenido = "\n".join(lineas) + "\n"

    ruta = REPORTES / f"informe-{ahora:%Y%m%d-%H%M%S}.md"
    ruta.write_text(contenido, encoding="utf-8")
    print(f"Informe creado: {ruta}")
    print(f"Coincidencias vigentes: {len(oportunidades)}; nuevas: {len(nuevas)}")

    if config.get("send_email", False):
        destino = config.get("email_to")
        if not destino:
            raise RuntimeError("Falta email_to en config.json")

        enviar_correo(
            destino,
            f"Publigraf Kenia: {len(nuevas)} nuevas oportunidades - {ahora:%d/%m/%Y}",
            contenido,
        )
        print(f"Correo enviado a {destino}")

        # Solo se marcan como notificadas después de enviar el correo.
        guardar_notificados(anteriores | {o["id"] for o in nuevas})
    else:
        print("Envío desactivado en config.json")


if __name__ == "__main__":
    main()
