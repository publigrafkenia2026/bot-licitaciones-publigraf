# Bot de licitaciones Publigraf Kenia

Proyecto inicial para preparar el monitoreo de oportunidades públicas relacionadas con impresión, papelería, publicidad, gran formato y merchandising.

## Estado actual

- Valida las categorías configuradas y genera un informe de prueba.
- Incluye ejecución manual y una programación diaria mediante GitHub Actions.
- **Todavía no consulta SEACE/OECE, no descarga documentos y no envía correos.**
- No agregues contraseñas, tokens ni archivos de credenciales al repositorio.

## Cómo probarlo en GitHub

1. Sube todos los archivos conservando las rutas.
2. Abre la pestaña **Actions**.
3. Si GitHub solicita habilitar workflows, pulsa **I understand my workflows, go ahead and enable them**.
4. Selecciona **Bot de licitaciones Publigraf** y pulsa **Run workflow**.
5. Abre la ejecución y revisa que termine en verde. Descarga el artefacto `informe-inicial-licitaciones`.

## Próximas etapas

1. Identificar fuentes oficiales actuales y verificar acceso permitido.
2. Implementar consulta y filtrado de convocatorias vigentes.
3. Encontrar documentos de requerimientos y descargar PDF disponibles.
4. Configurar Gmail y Drive mediante OAuth y secretos seguros.
5. Activar el envío diario después de pruebas satisfactorias.

La programación diaria de GitHub Actions puede retrasarse o desactivarse por inactividad en repositorios públicos. Verifica periódicamente la pestaña Actions.
