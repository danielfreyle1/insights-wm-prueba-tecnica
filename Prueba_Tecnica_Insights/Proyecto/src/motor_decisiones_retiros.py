
import pandas as pd
from datetime import timedelta


BUFFER_USD = 50
RECENT_DEST_DAYS = 7
DUP_WINDOW_MIN = 15


SEVERITY_MAP = {
    "KYC_NOT_VERIFIED": 100,
    "ACCOUNT_NOT_ACTIVE": 95,
    "UNWHITELISTED_HIGH_AML": 90,
    "INVALID_AMOUNT": 85,
    "DUPLICATE_REQUEST": 70,
    "INSUFFICIENT_SETTLED_AFTER_BUFFER": 65,
    "INSUFFICIENT_AVAILABLE_AFTER_BUFFER": 55,
    "DEST_CHANGED_RECENTLY": 45,
    "URGENT_RISK_TIER": 35,
}


def detectar_duplicados(df):
    """
    identifica solicitudes duplicadas segun la regla:
    mismo account_id + amount + destination_id dentro de 15 minutos
    """

    df = df.sort_values("created_at")

    df["created_at"] = pd.to_datetime(df["created_at"])

    duplicados = []

    for i in range(len(df)):
        fila = df.iloc[i]

        ventana = df[
            (df["account_id"] == fila["account_id"])
            & (df["amount"] == fila["amount"])
            & (df["destination_id"] == fila["destination_id"])
            & (df["created_at"] >= fila["created_at"] - timedelta(minutes=DUP_WINDOW_MIN))
            & (df["created_at"] <= fila["created_at"] + timedelta(minutes=DUP_WINDOW_MIN))
        ]

        duplicados.append(len(ventana) > 1)

    df["is_duplicate"] = duplicados

    return df


def evaluar_reglas(row):
    """
    aplica las reglas del ejercicio para determinar
    decision, reason_code y severity
    """

    # reglas de rechazo

    if row["account_status"] != "active":
        return "REJECT", "ACCOUNT_NOT_ACTIVE", SEVERITY_MAP["ACCOUNT_NOT_ACTIVE"]

    if row["kyc_status"] != "verified":
        return "REJECT", "KYC_NOT_VERIFIED", SEVERITY_MAP["KYC_NOT_VERIFIED"]

    if row["amount"] <= 0:
        return "REJECT", "INVALID_AMOUNT", SEVERITY_MAP["INVALID_AMOUNT"]

    if row["is_duplicate"]:
        return "REJECT", "DUPLICATE_REQUEST", SEVERITY_MAP["DUPLICATE_REQUEST"]

    if row["aml_risk_tier"] == "high" and not row["is_whitelisted"]:
        return "REJECT", "UNWHITELISTED_HIGH_AML", SEVERITY_MAP["UNWHITELISTED_HIGH_AML"]

    # reglas de hold

    if row["available_cash"] - row["amount"] < BUFFER_USD:
        return "HOLD", "INSUFFICIENT_AVAILABLE_AFTER_BUFFER", SEVERITY_MAP["INSUFFICIENT_AVAILABLE_AFTER_BUFFER"]

    if row["settled_cash"] - row["amount"] < BUFFER_USD:
        return "HOLD", "INSUFFICIENT_SETTLED_AFTER_BUFFER", SEVERITY_MAP["INSUFFICIENT_SETTLED_AFTER_BUFFER"]

    if row["destino_reciente"]:
        return "HOLD", "DEST_CHANGED_RECENTLY", SEVERITY_MAP["DEST_CHANGED_RECENTLY"]

    if row["requested_speed"] == "urgent" and row["aml_risk_tier"] in ["medium", "high"]:
        return "HOLD", "URGENT_RISK_TIER", SEVERITY_MAP["URGENT_RISK_TIER"]

    return "APPROVE", None, 0


def construir_motor_decisiones(
    withdrawal_requests,
    account_snapshot,
    destination_registry,
):
    """
    construye la tabla final de decisiones
    """

    df = withdrawal_requests.merge(
        account_snapshot, on="account_id", how="left")

    df = df.merge(destination_registry, on="destination_id", how="left")

    df = detectar_duplicados(df)

    df["as_of"] = pd.to_datetime(df["as_of"])
    df["last_changed_at"] = pd.to_datetime(df["last_changed_at"])

    df["destino_reciente"] = (
        (df["as_of"] - df["last_changed_at"]).dt.days < RECENT_DEST_DAYS
    )

    decisiones = df.apply(evaluar_reglas, axis=1)

    df["decision"] = decisiones.apply(lambda x: x[0])
    df["reason_code"] = decisiones.apply(lambda x: x[1])
    df["severity"] = decisiones.apply(lambda x: x[2])

    return df[["request_id", "decision", "reason_code", "severity"]]
