import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from supabase import create_client, Client

def generar_timestamps(mes, fechas_a_evitar=None):
    """
    Genera cuatro timestamps para cada día laboral de un mes especificado (lunes a viernes),
    excluyendo los días especificados en `fechas_a_evitar`.

    Args:
        mes (int): Mes del que se generarán los timestamps (1-12).
        fechas_a_evitar (list): Lista de fechas (tipo datetime.date) a evitar.

    Returns:
        list: Lista de timestamps generados.
    """
    # Rango de minutos para cada horario
    rangos = {
        8: (-10, 2),  # 8 am
        12: (-2, 2),  # 12 pm
        13: (-2, 2),  # 1 pm
        17: (-1, 6)   # 5 pm
    }
    
    # Lista para almacenar los timestamps generados
    timestamps = []
    
    # Validar y preparar las fechas a evitar
    if fechas_a_evitar is None:
        fechas_a_evitar = []
    fechas_a_evitar = set(fechas_a_evitar)  # Convertir a conjunto para búsqueda eficiente
    
    # Generar las fechas del mes
    year = datetime.now().year  # Año actual
    start_date = datetime(year, mes, 1)
    end_date = datetime(year, mes + 1, 1) if mes < 12 else datetime(year + 1, 1, 1)
    current_date = start_date
    
    while current_date < end_date:
        # Si es lunes a viernes y no está en las fechas a evitar
        if current_date.weekday() < 5 and current_date.date() not in fechas_a_evitar:
            for hour, (min_offset_start, min_offset_end) in rangos.items():
                # Generar el offset aleatorio de minutos y segundos
                minute_offset = random.randint(min_offset_start, min_offset_end)
                second_offset = random.randint(0, 59)
                # Crear el timestamp con el offset aplicado
                timestamp = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                timestamp += timedelta(minutes=minute_offset, seconds=second_offset)
                timestamps.append(timestamp)
        current_date += timedelta(days=1)
    
    return timestamps

def ajustar_horas_suplementarias(timestamps, horas_requeridas):
    """
    Ajusta los timestamps de Salida Final distribuyendo las horas extras necesarias,
    sumando 2 horas por día y colocando el sobrante en el último día.

    Args:
        timestamps (list): Lista de timestamps donde cada 4 representan un día laboral:
                           [Entrada Inicial, Salida Inicial, Entrada Inicial, Salida Final, ...].
        horas_requeridas (float): Total de horas extras requeridas (puede incluir decimales).

    Returns:
        list: Lista de timestamps actualizada con las horas extras ajustadas.
    """
    if len(timestamps) % 4 != 0:
        raise ValueError("La lista de timestamps debe tener un múltiplo de 4 elementos (4 por día laboral).")
    
    # Inicializar horas extras restantes
    horas_extras_restantes = horas_requeridas
    
    # Iterar sobre los días
    for i in range(3, len(timestamps), 4):  # Índices de Salida Final
        if horas_extras_restantes <= 0:
            break
        
        if horas_extras_restantes >= 2:
            # Sumar 2 horas al timestamp de Salida Final
            timestamps[i] += timedelta(hours=2)
            horas_extras_restantes -= 2
        else:
            # Sumar el sobrante (menos de 2 horas) al último día necesario
            timestamps[i] += timedelta(hours=horas_extras_restantes)
            horas_extras_restantes = 0

    # Verificar si se cubrieron todas las horas requeridas
    if horas_extras_restantes > 0:
        raise ValueError("No hay suficientes días para ajustar todas las horas extras requeridas.")

    return timestamps


def horas_extraordinarias(dias_disponibles, cantidad_horas, mes):
    """
    Crea timestamps para los días específicos del mes proporcionados, con horarios de 9am a 1pm o ajustados a 5 horas
    si los días no son suficientes para cubrir las horas extras requeridas.

    Args:
        dias_disponibles (list): Lista de días (números del mes) en los que se generarán los horarios.
        cantidad_horas (float): Cantidad de horas extras a generar.
        mes (int): Mes para el que se generarán los horarios (1-12).

    Returns:
        list: Lista plana de timestamps generados.
    """
    if not dias_disponibles:
        raise ValueError("La lista de días disponibles no puede estar vacía.")

    # Obtener el año actual
    year = datetime.now().year

    # Ordenar los días disponibles
    dias_disponibles = sorted(dias_disponibles)
    
    # Verificar si hay días suficientes
    horas_por_dia = 4
    if len(dias_disponibles) * horas_por_dia < cantidad_horas:
        horas_por_dia = 5  # Si no alcanzan, aumentar a 5 horas por día

    # Generar horarios
    timestamps = []
    horas_restantes = cantidad_horas
    for dia in dias_disponibles:
        if horas_restantes <= 0:
            break

        # Generar horarios para el día
        fecha = datetime(year, mes, dia)

        # Entrada
        entrada = fecha.replace(hour=9, minute=0, second=0, microsecond=0)
        entrada += timedelta(minutes=random.randint(-6, 7), seconds=random.randint(0, 59))

        # Salida (ajustada según las horas restantes)
        if horas_restantes >= horas_por_dia:
            salida = entrada + timedelta(hours=horas_por_dia)
            horas_restantes -= horas_por_dia
        else:
            salida = entrada + timedelta(hours=horas_restantes)
            horas_restantes = 0
        
        # Aleatorizar la salida (sumar -2 a 3 minutos y 1-59 segundos)
        salida += timedelta(minutes=random.randint(-2, 4), seconds=random.randint(1, 59))

        # Agregar los timestamps generados a la lista plana
        timestamps.append(entrada)
        timestamps.append(salida)

    if horas_restantes > 0:
        raise ValueError("No hay suficientes días disponibles para cubrir todas las horas extras.")

    return timestamps

def unir_y_ordenar_timestamps(lista1, lista2):
    """
    Une dos listas planas de timestamps y las ordena por fecha.

    Args:
        lista1 (list): Primera lista de timestamps (tipo datetime).
        lista2 (list): Segunda lista de timestamps (tipo datetime).

    Returns:
        list: Lista combinada y ordenada de timestamps.
    """
    # Combinar las listas
    combinada = lista1 + lista2
    
    # Ordenar la lista combinada
    combinada.sort()
    
    return combinada
    
# Ejemplo de uso:
from datetime import date

mes = 10  # Octubre
fechas_a_evitar = [date(2024, 10, 11), date(2024, 10, 17), date(2024, 10, 18)]  # Fechas específicas a evitar

print("Timestamps generados:")
timestamps_octubre = generar_timestamps(mes, fechas_a_evitar)
for ts in timestamps_octubre:
    print(ts)

print("Timestamps suplementarios:")
horas_requeridas = 3.5 # Total de horas extras requeridas
dias_timestamps_actualizados = ajustar_horas_suplementarias(timestamps_octubre, horas_requeridas)
# Imprimir los resultados
for ts in dias_timestamps_actualizados:
    print(ts)

print("Timestamps extraordinarios:")
# Ejemplo de uso extraordinarios:
dias_disponibles = [5, 11, 12, 19, 26]  # Días específicos
cantidad_horas = 12  # Total de horas extras requeridas
mes = 10  # Octubre
horarios = horas_extraordinarias(dias_disponibles, cantidad_horas, mes)
# Imprimir los resultados
for dia_horarios in horarios:
    print(dia_horarios)
    #print([str(h) for h in dia_horarios])


print("Timestamps ordenados:")
timestamps_ordenados = unir_y_ordenar_timestamps(dias_timestamps_actualizados, horarios)

# Imprimir resultados
for ts in timestamps_ordenados:
    print(ts)


# Cargar variables de entorno
load_dotenv()

# Obtener URL y clave de Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

# Crear cliente de Supabase
supabase: Client = create_client(url, key)

# Probar conexión: Leer datos de una tabla
try:
    response = supabase.table("nombre_de_tu_tabla").select("*").limit(1).execute()
    if response.data:
        print("¡Conexión exitosa! Aquí está una muestra de tus datos:")
        print(response.data)
    else:
        print("¡Conexión exitosa, pero no hay datos en la tabla!")
except Exception as e:
    print("Error al conectar a Supabase:")
    print(e)