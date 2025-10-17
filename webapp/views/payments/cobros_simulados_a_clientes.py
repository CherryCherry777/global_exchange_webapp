import random
from typing import Any, Dict


def cobrar_al_cliente_tarjeta_nacional(monto: float, numero_tokenizado: str) -> Dict[str, Any]:
    """
    Simula el cobro a un cliente con tarjeta nacional.
    
    La función determina el resultado del pago según el último dígito del número tokenizado:
      - Termina en '1'  → éxito garantizado
      - Termina en '0'  → fallo garantizado
      - Otro dígito     → resultado aleatorio

    Args:
        numero_tokenizado (str): Número tokenizado de la tarjeta.

    Returns:
        dict: Diccionario con las claves:
            - success (bool): True si el pago fue exitoso, False si falló.
            - message (str): Mensaje descriptivo del resultado.
    """
    if not numero_tokenizado or not numero_tokenizado[-1].isdigit():
        return {
            "success": False,
            "message": "Número tokenizado inválido o no contiene dígitos finales válidos.",
        }

    ultimo_digito = int(numero_tokenizado[-1])

    if ultimo_digito == 0:
        return {
            "success": True,
            "message": "Pago procesado exitosamente con tarjeta nacional.",
        }

    elif ultimo_digito == 1:
        return {
            "success": False,
            "message": "El pago fue rechazado por la entidad emisora.",
        }

    else:
        exito = random.choice([True, False])
        if exito:
            return {
                "success": True,
                "message": "Pago autorizado aleatoriamente (modo simulación).",
            }
        else:
            return {
                "success": False,
                "message": "El pago no pudo completarse (resultado aleatorio).",
            }


def cobrar_al_cliente_billetera(numero_celular: str, pin: str | None = None) -> Dict[str, Any]:
    """
    Simula el cobro con una billetera electrónica que requiere PIN.

    Args:
        numero_celular (str): Número de celular de la billetera.
        pin (str | None): PIN ingresado por el usuario. Si no se pasa, se pedirá.

    Returns:
        dict:
            - success (bool): True si el cobro fue exitoso.
            - message (str): Mensaje informativo.
            - require_pin (bool): True si se debe pedir PIN.
            - allow_retry (bool): True si puede volver a intentar el PIN.
    """
    if not numero_celular:
        return {
            "success": False,
            "message": "Número de celular no válido.",
            "require_pin": False,
            "allow_retry": False,
        }

    # Si no se ingresó PIN todavía
    if pin is None:
        return {
            "success": False,
            "message": "Se requiere PIN para autorizar el pago.",
            "require_pin": True,
            "allow_retry": True,
        }

    # Validar formato del PIN
    if not pin.isdigit():
        return {
            "success": False,
            "message": "PIN inválido, debe contener solo números.",
            "require_pin": True,
            "allow_retry": True,
        }

    # Validar longitud del PIN
    if len(pin) != 4:
        return {
            "success": False,
            "message": "PIN inválido: debe tener exactamente 4 dígitos.",
            "require_pin": True,
            "allow_retry": True,
        }

    ultimo = int(pin[-1])

    if ultimo == 1:
        return {
            "success": False,
            "message": "PIN incorrecto. Intenta nuevamente.",
            "require_pin": True,
            "allow_retry": True,
        }

    if ultimo == 0:
        return {
            "success": True,
            "message": "Pago aprobado correctamente.",
            "require_pin": False,
            "allow_retry": False,
        }

    # Resultado aleatorio
    exito = random.choice([True, False])
    return {
        "success": exito,
        "message": "Pago aprobado (aleatorio)." if exito else "PIN incorrecto. Intenta nuevamente.",
        "require_pin": not exito,
        "allow_retry": not exito,
    }


def validar_id_transferencia(id_transferencia: str) -> Dict[str, Any]:
    """
    Simula la validación de un ID de transferencia bancaria.

    Reglas:
      - Termina en '0' → éxito garantizado.
      - Termina en '1' → fallo garantizado.
      - Otro dígito     → resultado aleatorio.

    Args:
        id_transferencia (str): ID ingresado por el usuario.

    Returns:
        dict: {
            "success" (bool): True si es válido, False si falla.
            "message" (str): Mensaje descriptivo.
        }
    """
    if not id_transferencia or not id_transferencia[-1].isdigit():
        return {
            "success": False,
            "message": "El ID de transferencia es inválido o no contiene un dígito final válido.",
        }

    ultimo_digito = int(id_transferencia[-1])

    if ultimo_digito == 0:
        return {
            "success": True,
            "message": "Transferencia validada exitosamente.",
        }

    elif ultimo_digito == 1:
        return {
            "success": False,
            "message": "El ID de transferencia fue rechazado por el sistema bancario.",
        }

    else:
        exito = random.choice([True, False])
        return {
            "success": exito,
            "message": (
                "Transferencia validada correctamente (modo simulación)."
                if exito else
                "La transferencia no pudo ser validada (resultado aleatorio)."
            ),
        }