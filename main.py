from datetime import date
from attendance import (
    generar_timestamps,
    ajustar_horas_suplementarias,
    calcula_horas_extraordinarias,
    unir_y_ordenar_timestamps,
    generar_excel,
)


def main():
    nombre = input("Ingrese nombre del empleado: ")
    cedula = input("Ingrese la cédula del empleado: ")
    id_empleado = int(input("Ingrese id del empleado: "))
    departamento = input("Ingrese departamento del empleado: ")
    anio = int(input("Ingrese el año: "))
    mes = int(input("Ingrese el mes (1-12): "))
    horas_suplementarias = float(input("Ingrese las horas suplementarias: "))
    dias_extraordinarias = input("Ingrese los días extraordinarios (separado por comas): ")
    horas_extraordinarias = float(input("Ingrese las horas extraordinarias: "))

    dias_extraordinarios = [int(dia.strip()) for dia in dias_extraordinarias.split(',') if dia.strip()]
    fechas_a_evitar = [date(anio, mes, dia) for dia in dias_extraordinarios]

    base = generar_timestamps(mes, anio, fechas_a_evitar)
    base = ajustar_horas_suplementarias(base, horas_suplementarias)
    extras = calcula_horas_extraordinarias(dias_extraordinarios, horas_extraordinarias, mes, anio)
    ordenados = unir_y_ordenar_timestamps(base, extras)
    generar_excel(ordenados, nombre, departamento, id_empleado, cedula)


if __name__ == "__main__":
    main()

