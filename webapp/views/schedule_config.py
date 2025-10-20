from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from webapp.models import EmailScheduleConfig, ExpiracionTransaccionConfig, LimiteIntercambioScheduleConfig


@login_required
def manage_schedule(request):
    """
    Panel unificado para:
    - Programación de correos automáticos
    - Reseteo global de límites de intercambio
    - Expiración automática de transacciones
    """
    email_config, _ = EmailScheduleConfig.objects.get_or_create(pk=1)
    limite_config = LimiteIntercambioScheduleConfig.get_solo()
    expiraciones = ExpiracionTransaccionConfig.objects.all()

    # --- Asegurar entradas por defecto ---
    if not expiraciones.exists():
        for medio, _ in ExpiracionTransaccionConfig.MEDIOS:
            ExpiracionTransaccionConfig.objects.get_or_create(medio=medio)

    expiraciones = ExpiracionTransaccionConfig.objects.all()

    # --- 1) Formulario de EmailScheduleConfig ---
    if "save_email" in request.POST:
        email_config.frequency = request.POST.get("frequency")
        email_config.hour = int(request.POST.get("hour", 8))
        email_config.minute = int(request.POST.get("minute", 0))

        if email_config.frequency == "custom":
            email_config.interval_minutes = int(request.POST.get("interval_minutes", 60))
            email_config.weekday = None
        elif email_config.frequency == "weekly":
            email_config.weekday = request.POST.get("weekday")
            email_config.interval_minutes = None
        else:
            email_config.weekday = None
            email_config.interval_minutes = None

        email_config.save()
        messages.success(request, "✅ Programación de correos actualizada.")
        return redirect("manage_schedule")

    # --- 2) Formulario de LimiteIntercambioScheduleConfig ---
    if "save_limites" in request.POST:
        limite_config.is_active = ("is_active" in request.POST)
        limite_config.frequency = request.POST.get("frequency")
        limite_config.hour = int(request.POST.get("hour", 0))
        limite_config.minute = int(request.POST.get("minute", 0))

        if limite_config.frequency == "monthly":
            limite_config.month_day = int(request.POST.get("month_day", 1))
        else:
            limite_config.month_day = None

        limite_config.save()
        messages.success(request, "✅ Temporizador global de límites actualizado.")
        return redirect("manage_schedule")

    # --- 3) Formulario de ExpiracionTransaccionConfig ---
    if "save_expiraciones" in request.POST:
        for item in expiraciones:
            nuevo = request.POST.get(item.medio)
            if nuevo and nuevo.isdigit():
                item.minutos_expiracion = int(nuevo)
                item.save()

        messages.success(request, "✅ Expiraciones de transacciones actualizadas.")
        return redirect("manage_schedule")

    print(limite_config)
    return render(request, "webapp/schedule_config/manage_schedule.html", {
        "email_config": email_config,
        "limite_config": limite_config,
        "expiraciones": expiraciones
    })

