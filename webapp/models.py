from django.contrib.auth.models import AbstractUser, Group
from django.db import models

#Las clases van aqui
#Los usuarios heredan AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class Role(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.group.name

 #Clase Monedas utlizada para guardar los tipos de monedas   
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Código")
    name = models.CharField(max_length=50, verbose_name="Nombre")
    symbol = models.CharField(max_length=5, verbose_name="Símbolo")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Tipo de cambio")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"   

#Clase Tipo de pago utilizada para definir los tipos de pagos a ser utilizados en el sistema, ejemplo efectivo, cheque y demas
#Obs: Actualmente se carga en duro los valores    
class PaymentType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Tipo de Pago")
    code = models.CharField(max_length=20, unique=True, verbose_name="Código")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pago"
    
    def __str__(self):
        return self.name

# Clase para almacenar el tipo de cotizacion de la moneda
class Quote(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, verbose_name="Moneda")
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE, verbose_name="Tipo de Pago")
    buy_rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Precio Compra")
    sell_rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Precio Venta")
    effective_date = models.DateField(verbose_name="Fecha Vigencia")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        unique_together = ['currency', 'payment_type', 'effective_date']
    
    def __str__(self):
        return f"{self.currency.code} - {self.payment_type.name} - {self.effective_date}"
    
#Añadir manualmente los datos de tipo de pago a la base de datos
#INSERT INTO public.webapp_paymenttype (id, "name", code, is_active) VALUES(1, 'Efectivo', 'CASH', true);
#INSERT INTO public.webapp_paymenttype (id, "name", code, is_active) VALUES(2, 'Cheque', 'CHECK', true);
#INSERT INTO public.webapp_paymenttype (id, "name", code, is_active) VALUES(3, 'Transferencia', 'TRANSFER', true);
#INSERT INTO public.webapp_paymenttype (id, "name", code, is_active) VALUES(4, 'Billetera Electrónica', 'EWALLET', true);
#INSERT INTO public.webapp_paymenttype (id, "name", code, is_active) VALUES(5, 'Tarjeta de Crédito', 'CREDIT_CARD', true);
