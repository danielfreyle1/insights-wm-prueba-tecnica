import numpy as np
import pandas as pd


def validar_suma_pesos(vector_pesos: np.ndarray) -> None:
    """
    valida que la suma de los pesos del portafolio sea igual a 1
    o muy cercana por tolerancia numerica.

    parametros:
    vector_pesos: arreglo con los pesos del portafolio

    retorno:
    no retorna valor. genera error si la suma no es valida
    """
    suma_pesos = vector_pesos.sum()

    if not np.isclose(suma_pesos, 1.0):
        raise ValueError(
            f"la suma de los pesos debe ser 1.0, pero se obtuvo {suma_pesos:.10f}"
        )


def calcular_retorno_esperado_activos(matriz_retornos: pd.DataFrame) -> np.ndarray:
    """
    calcula el retorno esperado de cada activo usando el promedio
    de los retornos simulados.

    parametros:
    matriz_retornos: dataframe con retornos simulados

    retorno:
    arreglo con el retorno esperado de cada activo
    """
    retornos_esperados = matriz_retornos.mean(axis=0).to_numpy(dtype=float)
    return retornos_esperados


def calcular_matriz_covarianza(matriz_retornos: pd.DataFrame) -> np.ndarray:
    """
    calcula la matriz de covarianza de los activos.

    parametros:
    matriz_retornos: dataframe con retornos simulados

    retorno:
    matriz de covarianza
    """
    matriz_covarianza = matriz_retornos.cov().to_numpy(dtype=float)
    return matriz_covarianza


def calcular_retorno_esperado_portafolio(vector_pesos: np.ndarray, retornos_esperados: np.ndarray) -> float:
    """
    calcula el retorno esperado del portafolio.

    formula:
    e[rp] = p' * mu

    parametros:
    vector_pesos: pesos del portafolio
    retornos_esperados: retorno esperado de cada activo

    retorno:
    retorno esperado del portafolio
    """
    retorno_esperado = vector_pesos @ retornos_esperados
    return float(retorno_esperado)


def calcular_volatilidad_esperada_portafolio(vector_pesos: np.ndarray, matriz_covarianza: np.ndarray) -> float:
    """
    calcula la volatilidad esperada del portafolio.

    formula:
    sigma_p = sqrt(p' * sigma * p)

    parametros:
    vector_pesos: pesos del portafolio
    matriz_covarianza: matriz de covarianza de los activos

    retorno:
    volatilidad esperada del portafolio
    """
    varianza_portafolio = vector_pesos.T @ matriz_covarianza @ vector_pesos
    volatilidad_esperada = np.sqrt(varianza_portafolio)
    return float(volatilidad_esperada)


def resumir_portafolio(
    nombre_portafolio: str,
    vector_pesos: np.ndarray,
    retornos_esperados: np.ndarray,
    matriz_covarianza: np.ndarray,
) -> dict:
    """
    consolida los principales resultados de un portafolio.

    parametros:
    nombre_portafolio: nombre del portafolio
    vector_pesos: pesos del portafolio
    retornos_esperados: retorno esperado por activo
    matriz_covarianza: matriz de covarianza

    retorno:
    diccionario con resultados del portafolio
    """
    validar_suma_pesos(vector_pesos)

    retorno_esperado = calcular_retorno_esperado_portafolio(
        vector_pesos, retornos_esperados)
    volatilidad_esperada = calcular_volatilidad_esperada_portafolio(
        vector_pesos, matriz_covarianza)
    activos_con_peso = int(np.count_nonzero(vector_pesos))

    return {
        "portafolio": nombre_portafolio,
        "suma_pesos": float(vector_pesos.sum()),
        "activos_con_peso": activos_con_peso,
        "retorno_esperado": retorno_esperado,
        "volatilidad_esperada": volatilidad_esperada,
    }
