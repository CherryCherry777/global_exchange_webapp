document.addEventListener("DOMContentLoaded", () => {
  const step1 = document.getElementById("step-1");
  const step2 = document.getElementById("step-2");
  const next = document.getElementById("next-step");
  const prev = document.getElementById("prev-step");

  const ind1 = document.getElementById("indicator-step1");
  const ind2 = document.getElementById("indicator-step2");

  next.addEventListener("click", () => {
    // Actualiza los datos de resumen
    document.getElementById("resumen-tipo").textContent =
      document.getElementById("input-tipo")?.value || "";

    document.getElementById("resumen-origen").textContent =
      `${document.getElementById("input-monto-origen")?.value || "-"} ${document.getElementById("input-moneda-origen")?.value || ""}`;

    document.getElementById("resumen-destino").textContent =
      `${document.getElementById("input-monto-destino")?.value || "-"} ${document.getElementById("input-moneda-destino")?.value || ""}`;

    document.getElementById("resumen-pago").textContent =
      document.getElementById("simu-metodo-pago")?.selectedOptions[0]?.text || "-";

    document.getElementById("resumen-cobro").textContent =
      document.getElementById("simu-metodo-cobro")?.selectedOptions[0]?.text || "-";

    // Cambia la vista
    step1.classList.add("d-none");
    step2.classList.remove("d-none");
    ind1.classList.remove("active");
    ind2.classList.add("active");
  });

  prev.addEventListener("click", () => {
    // Volver al paso anterior
    step2.classList.add("d-none");
    step1.classList.remove("d-none");
    ind2.classList.remove("active");
    ind1.classList.add("active");
  });
});
