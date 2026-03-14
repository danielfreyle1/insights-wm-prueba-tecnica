#!/usr/bin/env python3
"""
=============================================================
CHATBOT ACH — SECCIÓN 4  |  Plataforma Insights WM
=============================================================

Ejecución:
    python ach_chatbot.py

Comandos especiales durante la conversación:
    /simular_r01   Fuerza error R01 (fondos insuficientes)
    /simular_r03   Fuerza error R03 (cuenta no encontrada)
    /reset         Borra memoria de sesión guardada
    /ayuda         Muestra comandos disponibles
    salir          Cierra el programa
=============================================================
"""

import json
import os
import sys
import time
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# BASE DE DATOS DE ROUTING NUMBERS
# ─────────────────────────────────────────────────────────────
ROUTING_DB = {
    # Bank of America
    ("bank of america", "texas"):           "111000614",
    ("bank of america", "california"):      "121000358",
    ("bank of america", "new york"):        "021200339",
    ("bank of america", "florida"):         "063100277",
    ("bank of america", "north carolina"):  "053000219",
    # Chase
    ("chase", "texas"):                     "111000614",
    ("chase", "california"):                "322271627",
    ("chase", "new york"):                  "021000021",
    ("chase", "florida"):                   "267084131",
    ("chase", "illinois"):                  "071000013",
    # Wells Fargo
    ("wells fargo", "california"):          "121042882",
    ("wells fargo", "texas"):               "111900659",
    ("wells fargo", "florida"):             "063107513",
    ("wells fargo", "new york"):            "026012881",
    ("wells fargo", "georgia"):             "061000227",
    # Citibank
    ("citibank", "new york"):               "021000089",
    ("citibank", "nevada"):                 "322271724",
    ("citibank", "illinois"):               "271070801",
    # Bancos comunidad latina
    ("banco popular", "new york"):          "021502011",
    ("banco popular", "puerto rico"):       "021502011",
    ("banesco", "florida"):                 "067015779",
    ("ponce bank", "new york"):             "226070131",
    ("lone star", "texas"):                 "114911687",
    # Otros
    ("us bank", "minnesota"):               "091000022",
    ("us bank", "california"):              "122235821",
    ("td bank", "new jersey"):              "031201360",
    ("td bank", "new york"):                "026013673",
    ("td bank", "florida"):                 "067014822",
    ("pnc bank", "pennsylvania"):           "031000053",
}

# Para autocompletar sugerencias al usuario
BANCOS_VALIDOS  = sorted({b for b, _ in ROUTING_DB})
ESTADOS_VALIDOS = sorted({s for _, s in ROUTING_DB})

# ─────────────────────────────────────────────────────────────
# MEMORIA PERSISTENTE ENTRE SESIONES
# ─────────────────────────────────────────────────────────────
MEMORY_FILE = Path("session_memory.json")

def cargar_memoria() -> dict:
    if MEMORY_FILE.exists():
        try:
            return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"banco": None, "estado": None, "nombre": None}

def guardar_memoria(mem: dict) -> None:
    MEMORY_FILE.write_text(
        json.dumps(mem, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def borrar_memoria() -> None:
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()

# ─────────────────────────────────────────────────────────────
# HELPERS DE FORMATO Y UI
# ─────────────────────────────────────────────────────────────
ANCHO = 62

def linea(char="─"):
    print(char * ANCHO)

def bot(msg: str, pausa: float = 0.0):
    """Imprime el mensaje del bot con efecto typewriter suave."""
    print("\n🤖  Bot: ", end="", flush=True)
    for ch in msg:
        print(ch, end="", flush=True)
        time.sleep(0.012)
    print()
    if pausa:
        time.sleep(pausa)

def pedir(prompt: str = "") -> str:
    """Captura input del usuario con formato consistente."""
    try:
        val = input(f"\n👤  Tú: {prompt}").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nSesión cerrada por el usuario. ¡Hasta pronto!")
        sys.exit(0)
    return val

def cargando(msg: str = "Buscando en el sistema", segundos: float = 1.2):
    print(f"\n   ⏳  {msg}", end="", flush=True)
    pasos = int(segundos / 0.18)
    for _ in range(pasos):
        print(".", end="", flush=True)
        time.sleep(0.18)
    print(" listo.")

def caja(lineas: list[str]):
    """Imprime un cuadro de texto formateado."""
    print()
    print("   ┌" + "─" * (ANCHO - 4) + "┐")
    for l in lineas:
        print(f"   │  {l:<{ANCHO - 7}}│")
    print("   └" + "─" * (ANCHO - 4) + "┘")
    print()

# ─────────────────────────────────────────────────────────────
# LÓGICA DE ROUTING
# ─────────────────────────────────────────────────────────────
def buscar_banco(texto: str) -> str | None:
    """Detecta el banco mencionado en texto libre."""
    t = texto.lower()
    for b in BANCOS_VALIDOS:
        if b in t:
            return b
    # Coincidencia parcial (ej. "bofa" → "bank of america")
    alias = {
        "bofa": "bank of america",
        "boa":  "bank of america",
        "wf":   "wells fargo",
        "bpop": "banco popular",
    }
    for k, v in alias.items():
        if k in t:
            return v
    return None

def buscar_estado(texto: str) -> str | None:
    """Detecta el estado de EE.UU. mencionado en texto libre."""
    t = texto.lower()
    alias_estados = {
        "tx": "texas", "ca": "california", "fl": "florida",
        "ny": "new york", "nueva york": "new york",
        "il": "illinois", "pa": "pennsylvania", "nj": "new jersey",
        "nc": "north carolina", "mn": "minnesota", "pr": "puerto rico",
        "nv": "nevada", "ga": "georgia", "oh": "ohio",
    }
    for abr, nombre in alias_estados.items():
        if abr in t.split() or nombre in t:
            return nombre
    for s in ESTADOS_VALIDOS:
        if s in t:
            return s
    return None

def lookup_routing(banco: str, estado: str) -> str | None:
    return ROUTING_DB.get((banco.lower().strip(), estado.lower().strip()))

# ─────────────────────────────────────────────────────────────
# HISTORIAL CONVERSACIONAL (memoria en sesión)
# ─────────────────────────────────────────────────────────────
historial: list[dict] = []

def registrar(rol: str, texto: str):
    historial.append({"rol": rol, "texto": texto})

def mostrar_historial():
    print("\n" + "═" * ANCHO)
    print("  HISTORIAL DE CONVERSACIÓN")
    print("═" * ANCHO)
    for entrada in historial:
        icono = "🤖" if entrada["rol"] == "bot" else "👤"
        print(f"{icono}  {entrada['texto']}")
    print("═" * ANCHO + "\n")

# ─────────────────────────────────────────────────────────────
# MANEJO DE ERRORES NACHA
# ─────────────────────────────────────────────────────────────
def manejar_error(codigo: str, banco: str = "", monto: float = 0.0):
    """
    Emite los mensajes EXACTOS de la investigación para R01 y R03.
    """
    if codigo == "R01":
        registrar("bot", f"ERROR R01 — Fondos Insuficientes")
        caja([
            "⚠️   ERROR R01 — INSUFFICIENT FUNDS",
            "",
            f"Tu intento de depósito por ${monto:,.2f} no pudo",
            "completarse porque tu banco nos informó que no",
            "había fondos suficientes. Asegúrate de que el",
            "saldo esté disponible y vuelve a intentar.",
            "",
            "¿Qué puedes hacer?",
            "  1. Verificar tu saldo y esperar compensaciones.",
            "  2. Reducir el monto del depósito.",
            "  3. Reintentar en 24 horas.",
        ])

    elif codigo == "R03":
        registrar("bot", "ERROR R03 — Cuenta No Encontrada")
        caja([
            "⚠️   ERROR R03 — NO ACCOUNT / UNABLE TO LOCATE",
            "",
            "No pudimos procesar tu depósito porque los datos",
            "de la cuenta no coinciden con los registros de",
            "tu banco. Por favor, revisa cuidadosamente que",
            "el número de cuenta y de ruta coincidan con los",
            "de tu estado de cuenta o cheque.",
            "",
            "¿Qué puedes hacer?",
            "  1. Revisar el número en un cheque físico.",
            "  2. Verificar en tu app bancaria (Account Info).",
            "  3. Reiniciar el proceso con los datos corregidos.",
        ])

# ─────────────────────────────────────────────────────────────
# COMANDOS ESPECIALES
# ─────────────────────────────────────────────────────────────
def manejar_comando(cmd: str, banco: str = "", monto: float = 0.0) -> bool:
    """
    Retorna True si el input era un comando especial.
    """
    c = cmd.strip().lower()

    if c == "/simular_r01":
        manejar_error("R01", banco, monto if monto else 1000.0)
        return True

    if c == "/simular_r03":
        manejar_error("R03", banco, monto)
        return True

    if c == "/reset":
        borrar_memoria()
        bot("✅  Memoria de sesión borrada. Empezamos de cero.")
        return True

    if c == "/historial":
        mostrar_historial()
        return True

    if c == "/ayuda":
        caja([
            "COMANDOS DISPONIBLES",
            "",
            "  /simular_r01  →  Fuerza error R01 (fondos insuf.)",
            "  /simular_r03  →  Fuerza error R03 (cuenta inv.)",
            "  /reset        →  Borra memoria de sesión",
            "  /historial    →  Muestra el chat completo",
            "  /ayuda        →  Este menú",
            "  salir         →  Cierra el programa",
        ])
        return True

    return False

# ─────────────────────────────────────────────────────────────
# FLUJO PRINCIPAL
# ─────────────────────────────────────────────────────────────
def chatbot():
    memoria = cargar_memoria()

    # ── BIENVENIDA ────────────────────────────────────────────
    os.system("cls" if os.name == "nt" else "clear")
    print("═" * ANCHO)
    print("  🏦   INSIGHTS WM — ASISTENTE DE FONDEO ACH")
    print("       Escribe /ayuda para ver comandos")
    print("═" * ANCHO)

    # ── NOMBRE ────────────────────────────────────────────────
    if memoria.get("nombre"):
        nombre = memoria["nombre"]
        bot(f"¡Bienvenido de vuelta, {nombre}! 👋")
    else:
        bot("¡Hola! Soy el asistente de Insights WM. "
            "Te guiaré para configurar tu fondeo ACH. "
            "¿Cuál es tu nombre?")
        nombre = pedir()
        if not nombre:
            nombre = "cliente"
        bot(f"Mucho gusto, {nombre}.")
        memoria["nombre"] = nombre
        guardar_memoria(memoria)

    registrar("bot", f"Bienvenido, {nombre}.")

    # ── ESTADO 1: RECOPILACIÓN — BANCO ────────────────────────
    banco_norm = memoria.get("banco")

    if banco_norm:
        bot(f"Recuerdo que tu banco es {banco_norm.title()}. "
            "¿Es correcto, o quieres cambiar el banco? (sí / otro banco)")
        resp = pedir().lower()
        if resp not in ("sí", "si", "s", "yes", "y", "correcto", "ok"):
            banco_norm = None
            memoria["banco"] = None
            memoria["estado"] = None
            guardar_memoria(memoria)

    if not banco_norm:
        bot("Antes de darte cualquier dato de enrutamiento, "
            "necesito saber en qué banco tienes tu cuenta. "
            "¿En qué banco está tu cuenta? "
            "(Ej: Bank of America, Chase, Wells Fargo...)")

        while True:
            inp = pedir()

            if manejar_comando(inp):
                continue

            if inp.lower() in ("salir", "exit"):
                bot("¡Hasta pronto! 👋")
                sys.exit(0)

            banco_detectado = buscar_banco(inp)
            if banco_detectado:
                banco_norm = banco_detectado
                bot(f"Perfecto. Banco: {banco_norm.title()}.")
                registrar("usuario", f"Banco: {banco_norm}")
                memoria["banco"] = banco_norm
                guardar_memoria(memoria)
                break
            else:
                sugerencias = ", ".join(b.title() for b in BANCOS_VALIDOS[:6])
                bot(f"No reconocí ese banco. Bancos disponibles: {sugerencias}... "
                    "Por favor intenta de nuevo.")

    # ── ESTADO 1: RECOPILACIÓN — ESTADO ───────────────────────
    estado_norm = memoria.get("estado")

    if estado_norm:
        bot(f"También recuerdo que tu cuenta está registrada en "
            f"{estado_norm.title()}. ¿Correcto? (sí / otro estado)")
        resp = pedir().lower()
        if resp not in ("sí", "si", "s", "yes", "y", "correcto", "ok"):
            estado_norm = None
            memoria["estado"] = None
            guardar_memoria(memoria)

    if not estado_norm:
        bot(f"¿En qué estado de EE.UU. abriste originalmente tu cuenta "
            f"en {banco_norm.title()}? Un mismo banco puede tener "
            "routing numbers distintos por estado.")

        while True:
            inp = pedir()

            if manejar_comando(inp):
                continue

            if inp.lower() in ("salir", "exit"):
                bot("¡Hasta pronto! 👋")
                sys.exit(0)

            estado_detectado = buscar_estado(inp)
            if estado_detectado:
                estado_norm = estado_detectado
                bot(f"Perfecto. Estado: {estado_norm.title()}.")
                registrar("usuario", f"Estado: {estado_norm}")
                memoria["estado"] = estado_norm
                guardar_memoria(memoria)
                break
            else:
                bot("No reconocí ese estado. Ejemplos: Texas, California, "
                    "Florida, New York. Por favor intenta de nuevo.")

    # ── ESTADO 2: LOOKUP DE ROUTING ───────────────────────────
    cargando(f"Buscando routing para {banco_norm.title()} — {estado_norm.title()}")

    routing = lookup_routing(banco_norm, estado_norm)

    if routing:
        caja([
            "✅  ROUTING NUMBER ENCONTRADO",
            "",
            f"Banco:    {banco_norm.title()}",
            f"Estado:   {estado_norm.title()}",
            f"Routing:  {routing}",
            "",
            "⚠️  Verifica este número directamente con tu",
            "    banco antes de usarlo en transferencias.",
        ])
        registrar("bot", f"Routing encontrado: {routing}")
        bot(f"Tu routing number es {routing}. Anótalo.")
    else:
        bot(f"No encontré un routing para {banco_norm.title()} "
            f"en {estado_norm.title()} en nuestra base de datos. "
            "Consulta el número en un cheque (esquina inferior izquierda) "
            "o en la sección 'Account Details' de tu app bancaria.")
        registrar("bot", "Routing no encontrado — se aplicó protocolo manual.")

    # ── ESTADO 3: INSTRUCCIONES PASO A PASO ───────────────────
    bot("Ahora te guiaré para completar la configuración del ACH Pull. "
        "Son 5 pasos rápidos.")

    # Paso 1
    bot("Paso 1 — Nombre del titular: ¿Cuál es tu nombre completo "
        "exactamente como aparece en tu cuenta bancaria?")
    while True:
        titular = pedir("Nombre completo: ")
        if manejar_comando(titular):
            continue
        if titular.lower() in ("salir", "exit"):
            bot("¡Hasta pronto! 👋"); sys.exit(0)
        if len(titular) >= 3:
            registrar("usuario", f"Titular: {titular}")
            bot(f"Registrado: {titular}")
            break
        bot("Por favor ingresa tu nombre completo.")

    # Paso 2
    bot("Paso 2 — Tipo de cuenta: ¿Es Checking (cuenta de cheques) "
        "o Savings (cuenta de ahorros)?")
    while True:
        tipo_raw = pedir("Checking o Savings: ").lower()
        if manejar_comando(tipo_raw):
            continue
        if tipo_raw in ("salir", "exit"):
            bot("¡Hasta pronto! 👋"); sys.exit(0)
        if "check" in tipo_raw or "cheque" in tipo_raw or tipo_raw == "c":
            tipo_cuenta = "Checking"
            break
        elif "sav" in tipo_raw or "ahorro" in tipo_raw or tipo_raw == "s":
            tipo_cuenta = "Savings"
            break
        else:
            bot("Por favor escribe 'Checking' o 'Savings'.")
    registrar("usuario", f"Tipo: {tipo_cuenta}")
    bot(f"Tipo de cuenta: {tipo_cuenta}.")

    # Paso 3
    bot("Paso 3 — Número de cuenta: Ingresa tu Account Number. "
        "Lo encuentras en un cheque (segunda serie de números) "
        "o en tu app en 'Account Details'.")
    while True:
        num_cuenta = pedir("Número de cuenta: ")
        if manejar_comando(num_cuenta):
            continue
        if num_cuenta.lower() in ("salir", "exit"):
            bot("¡Hasta pronto! 👋"); sys.exit(0)
        if num_cuenta.replace("-", "").replace(" ", "").isdigit() and len(num_cuenta) >= 4:
            registrar("usuario", f"Cuenta: ****{num_cuenta[-4:]}")
            bot(f"Número registrado: ****{num_cuenta[-4:]}")
            break
        bot("El número de cuenta debe contener solo dígitos. Intenta de nuevo.")

    # Paso 4
    bot(f"Paso 4 — Routing number: Confirma que el routing es "
        f"{routing if routing else 'el que obtuviste de tu banco'}. "
        "¿Es correcto? (sí / no)")
    while True:
        conf_routing = pedir().lower()
        if manejar_comando(conf_routing):
            continue
        if conf_routing in ("sí", "si", "s", "yes", "y", "correcto", "ok"):
            bot("Routing confirmado. ✅")
            break
        elif conf_routing in ("no", "n"):
            nuevo_routing = pedir("Ingresa el routing correcto (9 dígitos): ")
            if nuevo_routing.isdigit() and len(nuevo_routing) == 9:
                routing = nuevo_routing
                bot(f"Routing actualizado: {routing}. ✅")
                break
            else:
                bot("El routing debe tener exactamente 9 dígitos.")
        else:
            bot("Por favor responde 'sí' o 'no'.")

    # Paso 5
    bot("Paso 5 — Autorización: Para completar la configuración, "
        "debes aceptar el mandato electrónico (SEC Code WEB) que autoriza "
        "a Insights a realizar débitos desde tu cuenta. "
        "Tus fondos estarán disponibles para invertir de inmediato "
        "(Instant Buying Power), pero para retiros aplica un período "
        "de retención de 3 a 5 días hábiles. "
        "¿Aceptas los términos? (sí / no)")
    while True:
        acept = pedir().lower()
        if manejar_comando(acept):
            continue
        if acept in ("sí", "si", "s", "yes", "y"):
            bot("Autorización registrada. ✅")
            registrar("bot", "Mandato electrónico aceptado.")
            break
        elif acept in ("no", "n"):
            bot("Sin la autorización no podemos proceder. "
                "Si tienes dudas, contacta a support@insightswm.com.")
            sys.exit(0)
        else:
            bot("Por favor responde 'sí' o 'no'.")

    # ── ESTADO 4: CONFIRMACIÓN ────────────────────────────────
    import random
    ref_id = f"ACH{random.randint(100000, 999999)}"

    caja([
        "📋  RESUMEN DE CONFIGURACIÓN ACH PULL",
        "",
        f"Titular:    {titular}",
        f"Banco:      {banco_norm.title()}",
        f"Estado:     {estado_norm.title()}",
        f"Tipo:       {tipo_cuenta}",
        f"Cuenta:     ****{num_cuenta[-4:]}",
        f"Routing:    {routing}",
        "",
        "¿Confirmas que todos los datos son correctos?",
    ])

    bot("¿Confirmas? (sí / no)")
    while True:
        conf_final = pedir().lower()
        if manejar_comando(conf_final):
            continue
        if conf_final in ("sí", "si", "s", "yes", "y"):
            break
        elif conf_final in ("no", "n"):
            bot("Proceso cancelado. Puedes reiniciar cuando quieras.")
            sys.exit(0)
        else:
            bot("Por favor responde 'sí' o 'no'.")

    # ── PROCESAMIENTO SIMULADO ────────────────────────────────
    cargando("Procesando configuración en la red Nacha", 1.8)

    # Aquí se puede forzar un error con /simular_r01 o /simular_r03
    # Para demo se muestra éxito directamente
    caja([
        "✅  CONFIGURACIÓN ACH EXITOSA",
        "",
        f"ID de referencia:  {ref_id}",
        f"Titular:           {titular}",
        f"Banco:             {banco_norm.title()} — {estado_norm.title()}",
        f"Cuenta:            ****{num_cuenta[-4:]}",
        f"Routing:           {routing}",
        "",
        "Instant Buying Power:  Activo de inmediato",
        "Retiro disponible:     3-5 días hábiles",
        "",
        "Recibirás confirmación por email.",
    ])

    registrar("bot", f"Configuración exitosa. Ref: {ref_id}")
    bot(f"¡Listo, {nombre}! Tu cuenta ACH está configurada. "
        f"Guarda tu referencia: {ref_id}")

    # ── ESTADO 5: MANEJO DE FALLOS (demo interactivo) ─────────
    bot("¿Quieres probar los escenarios de error? "
        "Escribe /simular_r01 o /simular_r03 para verlos, "
        "o escribe 'no' para terminar.")

    while True:
        inp = pedir()
        if manejar_comando(inp, banco=banco_norm):
            bot("¿Quieres probar otro escenario o prefieres terminar? (otro / terminar)")
            continue
        if inp.lower() in ("no", "terminar", "salir", "exit", "n"):
            break
        bot("Escribe /simular_r01, /simular_r03 o 'terminar'.")

    # ── CIERRE ────────────────────────────────────────────────
    linea("═")
    print("  Sesión finalizada — Insights WM ACH Assistant")
    linea("═")
    bot(f"¡Hasta pronto, {nombre}! 👋 "
        "Tu información quedó guardada para la próxima sesión.")


# ─────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chatbot()
