import random
from ...models import Transaccion, BilleteraCobro, CuentaBancariaCobro, Tauser

def procesar_transferencia(transaccion: Transaccion, metodo_cobro) -> bool:
    """
    Simula el procesamiento de una transferencia bancaria.
    Retorna True si fue exitosa, False si falló.
    """

    numero = str(metodo_cobro.numero_cuenta or "").strip()
    if not numero:
        raise ValueError("El medio de cobro no tiene un número de cuenta válido.")

    ultimo = numero[-1]

    if ultimo == "1":
        # Fuerza un fallo
        return False
    elif ultimo == "0":
        # Fuerza éxito
        return True
    else:
        # Simula resultado aleatorio (50% probabilidad)
        return random.choice([True, False])


def procesar_billetera(transaccion: Transaccion, metodo_cobro) -> bool:
    """
    Simula el procesamiento de una transferencia a la billetera del cliente.
    Retorna True si fue exitosa, False si falló.
    """

    numero = str(metodo_cobro.numero_celular or "").strip()
    if not numero:
        raise ValueError("El medio de cobro no tiene un número de cuenta válido.")

    ultimo = numero[-1]

    if ultimo == "1":
        # Fuerza un fallo
        return False
    elif ultimo == "0":
        # Fuerza éxito
        return True
    else:
        # Simula resultado aleatorio (50% probabilidad)
        return random.choice([True, False])



def procesar_pago_cliente(transaccion: Transaccion) -> bool:
    """
    Procesa el pago de la casa al cliente, según el medio de cobro asociado.
    Retorna True si fue exitoso, False en caso contrario.
    """

    # Asegurarse de tener los datos sincronizados
    transaccion.refresh_from_db()

    # Resolver el objeto metodo_cobro manualmente (más robusto)
    model_class = transaccion.medio_cobro_type.model_class()
    metodo_cobro = model_class.objects.get(pk=transaccion.medio_cobro_id)

    # Ejecutar según el tipo concreto
    if isinstance(metodo_cobro, CuentaBancariaCobro):
        return procesar_transferencia(transaccion, metodo_cobro)
    elif isinstance(metodo_cobro, BilleteraCobro):
        return procesar_billetera(transaccion, metodo_cobro)
    else:
        raise ValueError(f"Tipo de cobro desconocido: {type(metodo_cobro).__name__}")