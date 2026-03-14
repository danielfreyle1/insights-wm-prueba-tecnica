import pandas as pd
import numpy as np


def cargar_matriz_simulacion(ruta_archivo: str, nombre_hoja: str = "Matriz de Simulacion") -> pd.DataFrame:
    """
    carga la matriz de retornos simulados desde una hoja de excel.

    parametros:
    ruta_archivo: ruta del archivo excel
    nombre_hoja: nombre de la hoja donde esta la matriz de simulacion

    retorno:
    dataframe con las simulaciones de retornos de los activos
    """
    matriz = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja)
    return matriz


def cargar_vector_pesos(ruta_archivo: str, nombre_hoja: str) -> np.ndarray:
    """
    carga el vector de pesos de un portafolio desde una hoja de excel.

    parametros:
    ruta_archivo: ruta del archivo excel
    nombre_hoja: nombre de la hoja donde estan los pesos

    retorno:
    arreglo de numpy con los pesos del portafolio
    """
    pesos = pd.read_excel(ruta_archivo, sheet_name=nombre_hoja)
    return pesos.iloc[0].to_numpy(dtype=float)
