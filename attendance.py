"""Utility functions for generating attendance data and Excel reports."""

import os
import random
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Configure locale for month/day names in Spanish if available
try:
    import locale
    locale.setlocale(locale.LC_TIME, 'es_ES.utf8')
except Exception:
    pass

__all__ = [
    "generar_timestamps",
    "ajustar_horas_suplementarias",
    "calcula_horas_extraordinarias",
    "unir_y_ordenar_timestamps",
    "generar_excel",
    "subir_timestamps_a_supabase",
]


def generar_timestamps(mes: int, año: int, fechas_a_evitar: Optional[List[datetime.date]] = None) -> List[datetime]:
    """Generate four timestamps for each working day of the given month."""
    rangos = {
        8: (-10, 2),  # 8 am
        12: (-2, 2),  # 12 pm
        13: (-2, 2),  # 1 pm
        17: (-1, 6)   # 5 pm
    }
    timestamps: List[datetime] = []
    if fechas_a_evitar is None:
        fechas_a_evitar = []
    fechas_a_evitar = set(fechas_a_evitar)
    start_date = datetime(año, mes, 1)
    end_date = datetime(año, mes + 1, 1) if mes < 12 else datetime(año + 1, 1, 1)
    current_date = start_date
    while current_date < end_date:
        if current_date.weekday() < 5 and current_date.date() not in fechas_a_evitar:
            for hour, (min_start, min_end) in rangos.items():
                minute_offset = random.randint(min_start, min_end)
                second_offset = random.randint(0, 59)
                ts = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                ts += timedelta(minutes=minute_offset, seconds=second_offset)
                timestamps.append(ts)
        current_date += timedelta(days=1)
    return timestamps


def ajustar_horas_suplementarias(timestamps: List[datetime], horas_requeridas: float) -> List[datetime]:
    """Adjust timestamps by distributing overtime across days."""
    if len(timestamps) % 4 != 0:
        raise ValueError("La lista de timestamps debe tener un múltiplo de 4 elementos (4 por día laboral).")
    horas_extras_restantes = horas_requeridas
    for i in range(3, len(timestamps), 4):
        if horas_extras_restantes <= 0:
            break
        if horas_extras_restantes >= 2:
            timestamps[i] += timedelta(hours=2)
            horas_extras_restantes -= 2
        else:
            timestamps[i] += timedelta(hours=horas_extras_restantes)
            horas_extras_restantes = 0
    if horas_extras_restantes > 0:
        raise ValueError("No hay suficientes días para ajustar todas las horas extras requeridas.")
    return timestamps


def calcula_horas_extraordinarias(dias_disponibles: List[int], cantidad_horas: float, mes: int, año: int) -> List[datetime]:
    """Generate overtime timestamps for specific days."""
    if not dias_disponibles:
        raise ValueError("La lista de días disponibles no puede estar vacía.")
    dias_disponibles = sorted(dias_disponibles)
    horas_por_dia = 4
    if len(dias_disponibles) * horas_por_dia < cantidad_horas:
        horas_por_dia = 5
    timestamps: List[datetime] = []
    horas_restantes = cantidad_horas
    for dia in dias_disponibles:
        if horas_restantes <= 0:
            break
        fecha = datetime(año, mes, int(dia))
        entrada = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        entrada += timedelta(minutes=random.randint(-6, 7), seconds=random.randint(0, 59))
        if horas_restantes >= horas_por_dia:
            salida = entrada + timedelta(hours=horas_por_dia)
            horas_restantes -= horas_por_dia
        else:
            salida = entrada + timedelta(hours=horas_restantes)
            horas_restantes = 0
        salida += timedelta(minutes=random.randint(-2, 4), seconds=random.randint(1, 59))
        timestamps.append(entrada)
        timestamps.append(salida)
    if horas_restantes > 0:
        raise ValueError("No hay suficientes días disponibles para cubrir todas las horas extras.")
    return timestamps


def unir_y_ordenar_timestamps(lista1: List[datetime], lista2: List[datetime]) -> List[datetime]:
    """Combine and sort timestamp lists."""
    combinada = lista1 + lista2
    combinada.sort()
    return combinada


def generar_excel(lista_timestamps: List[datetime], nombre_empleado: str, departamento: str, id_empleado: int, cedula: str) -> str:
    """Generate an Excel report with attendance data."""
    if not lista_timestamps:
        raise ValueError("La lista de timestamps está vacía.")
    mes = lista_timestamps[0].strftime("%B").capitalize()
    anio = lista_timestamps[0].year
    encabezado = f"{nombre_empleado.replace(' ', '_')}_{mes.upper()}_{anio}"
    nombre_archivo = f"{encabezado}.xlsx"
    datos = []
    for i, ts in enumerate(lista_timestamps):
        fecha = ts.strftime("%Y-%m-%d")
        hora = ts.strftime("%H:%M:%S")
        dia = ts.strftime("%A").capitalize()
        tipo = "ENTRADA" if i % 2 == 0 else "SALIDA"
        datos.append({
            "ID": id_empleado,
            "Nombre del empleado": nombre_empleado,
            "Nombre de la empresa": "ZOENETV S.A.",
            "Departamento": departamento,
            "Día": dia,
            "Fecha": fecha,
            "Hora de marcación": hora,
            "Tipo de marcación": tipo,
        })
    with pd.ExcelWriter(nombre_archivo, engine="xlsxwriter") as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet("Marcaciones")
        writer.sheets["Marcaciones"] = worksheet
        filas_adicionales = [
            "HORARIO LABORAL DE ZOENETV S.A.",
            "RUC: 1792612454001",
            f"MES: {mes.upper()} {anio}",
            f"EMPLEADO: {nombre_empleado}",
            f"CÉDULA: {cedula}",
            f"DEPARTAMENTO: {departamento.upper()}",
        ]
        for row_num, texto in enumerate(filas_adicionales):
            worksheet.write(row_num, 0, texto)
        inicio_tabla = len(filas_adicionales) + 2
        columnas = [
            "ID", "Nombre del empleado", "Nombre de la empresa",
            "Departamento", "Día", "Fecha", "Hora de marcación", "Tipo de marcación",
        ]
        for col_num, column_title in enumerate(columnas):
            worksheet.write(inicio_tabla, col_num, column_title)
        for row_num, fila in enumerate(datos, start=inicio_tabla + 1):
            worksheet.write(row_num, 0, fila["ID"])
            worksheet.write(row_num, 1, fila["Nombre del empleado"])
            worksheet.write(row_num, 2, fila["Nombre de la empresa"])
            worksheet.write(row_num, 3, fila["Departamento"])
            worksheet.write(row_num, 4, fila["Día"])
            worksheet.write(row_num, 5, fila["Fecha"])
            worksheet.write(row_num, 6, fila["Hora de marcación"])
            worksheet.write(row_num, 7, fila["Tipo de marcación"])
        max_row = len(datos) + inicio_tabla + 2
        worksheet.write(max_row, 1, "Firma del Empleado:")
        worksheet.write(max_row + 4, 1, nombre_empleado)
        worksheet.write(max_row + 5, 1, cedula)
        worksheet.write(max_row, 5, "Firma del Control:")
        worksheet.write(max_row + 4, 5, "Analista de TTHH")
    return nombre_archivo


# --- Supabase helper -------------------------------------------------------
_load_attempted = False
_supabase_client: Optional[Client] = None


def _get_supabase() -> Optional[Client]:
    global _load_attempted, _supabase_client
    if _supabase_client or _load_attempted:
        return _supabase_client
    _load_attempted = True
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if url and key:
        _supabase_client = create_client(url, key)
    return _supabase_client


def subir_timestamps_a_supabase(timestamps: List[datetime], employee_id: int) -> None:
    """Upload timestamps to Supabase."""
    client = _get_supabase()
    if client is None:
        raise RuntimeError("Supabase credentials no configurados")
    data = []
    for i, ts in enumerate(timestamps):
        tipo = "ENTRADA" if i % 2 == 0 else "SALIDA"
        data.append({"employee_id": employee_id, "date": ts.isoformat(), "type": tipo})
    resp = client.table("attendances").insert(data).execute()
    if resp.get("status_code") != 201:
        raise RuntimeError(f"Error al subir los datos: {resp.get('error')}")

