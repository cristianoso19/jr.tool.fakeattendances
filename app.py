from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from datetime import date
from io import BytesIO

from attendance import (
    generar_timestamps,
    ajustar_horas_suplementarias,
    calcula_horas_extraordinarias,
    unir_y_ordenar_timestamps,
    generar_excel,
)

app = FastAPI(title="Attendance Tool")

HTML_FORM = """
<!doctype html>
<html>
<head><title>Generador de Asistencias</title></head>
<body>
<h2>Generador de Asistencias</h2>
<form action="/generate" method="post">
  Nombre: <input type="text" name="nombre" required><br>
  Cédula: <input type="text" name="cedula" required><br>
  ID Empleado: <input type="number" name="id_empleado" required><br>
  Departamento: <input type="text" name="departamento" required><br>
  Año: <input type="number" name="anio" required><br>
  Mes: <input type="number" name="mes" min="1" max="12" required><br>
  Horas suplementarias: <input type="number" name="horas_sup" step="0.1" value="0"><br>
  Días extraordinarios (ej: 5,11): <input type="text" name="dias_extra" value=""><br>
  Horas extraordinarias: <input type="number" name="horas_extra" step="0.1" value="0"><br>
  <button type="submit">Generar</button>
</form>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_FORM


@app.post("/generate")
def generate(
    nombre: str = Form(...),
    cedula: str = Form(...),
    id_empleado: int = Form(...),
    departamento: str = Form(...),
    anio: int = Form(...),
    mes: int = Form(...),
    horas_sup: float = Form(0),
    dias_extra: str = Form(""),
    horas_extra: float = Form(0),
):
    try:
        dias_lista = [int(d.strip()) for d in dias_extra.split(',') if d.strip()]
        fechas_a_evitar = [date(anio, mes, d) for d in dias_lista]
        base = generar_timestamps(mes, anio, fechas_a_evitar)
        base = ajustar_horas_suplementarias(base, horas_sup)
        extras = calcula_horas_extraordinarias(dias_lista, horas_extra, mes, anio) if horas_extra else []
        ordenados = unir_y_ordenar_timestamps(base, extras)
        excel_bytes = generar_excel(
            ordenados,
            nombre,
            departamento,
            id_empleado,
            cedula,
            in_memory=True,
        )
        mes_txt = ordenados[0].strftime("%B").capitalize()
        anio_txt = ordenados[0].year
        filename = f"{nombre.replace(' ', '_')}_{mes_txt.upper()}_{anio_txt}.xlsx"
        headers = {"Content-Disposition": f"attachment; filename=\"{filename}\""}
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )
    except Exception as exc:
        return HTMLResponse(f"<h3>Error: {exc}</h3>", status_code=400)
