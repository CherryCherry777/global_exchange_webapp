import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def procesar_pago_stripe(
    *,
    cliente_stripe_id: str,
    metodo_pago_id: str,
    monto: float,
    moneda: str,
    descripcion: str,
) -> dict:
    """
    Crea y confirma un PaymentIntent en Stripe para un cliente con un método de pago guardado.

    Args:
        cliente_stripe_id: ID del cliente en Stripe (customer_id).
        metodo_pago_id: ID del método de pago guardado (payment_method_id).
        monto: Monto a cobrar (en unidades de la moneda, no en centavos).
        moneda: Código de moneda (ej. 'pyg', 'usd').
        descripcion: Descripción del pago (ej. 'Compra de divisas').

    Returns:
        dict con:
            - success (bool): True si el pago fue confirmado.
            - payment_intent_id (str): ID del PaymentIntent creado.
            - message (str): Mensaje de éxito o error.
    """
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=int(monto),  # Stripe trabaja en centavos
            currency=moneda.lower(),
            customer=cliente_stripe_id,
            payment_method=metodo_pago_id,
            off_session=True,
            confirm=True,  # confirmación automática
            description=descripcion,
        )

        return {
            "success": True,
            "payment_intent_id": payment_intent.id,
            "message": "Pago confirmado correctamente.",
        }


    except stripe.CardError as e:
        # En la nueva versión, e.user_message da un mensaje legible al usuario
        return {
            "success": False,
            "payment_intent_id": None,
            "message": f"Error de tarjeta: {e.user_message}",
        }

    except stripe.StripeError as e:
        return {
            "success": False,
            "payment_intent_id": None,
            "message": f"Error general de Stripe: {str(e)}",
        }

    except Exception as e:
        return {
            "success": False,
            "payment_intent_id": None,
            "message": f"Error inesperado: {str(e)}",
        }