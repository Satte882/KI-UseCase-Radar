document.addEventListener("DOMContentLoaded", () => {
  const attachSubmitGuard = (form, { buttonLabel, statusLabel = "" }) => {
    form.addEventListener("submit", (event) => {
      if (form.dataset.submitted === "true") {
        event.preventDefault();
        return;
      }

      const button = form.querySelector('button[type="submit"], button:not([type])');
      if (!button || button.disabled) {
        return;
      }

      form.dataset.submitted = "true";
      button.disabled = true;
      button.setAttribute("aria-busy", "true");

      if (statusLabel) {
        button.innerHTML =
          '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> ' +
          `<span>${buttonLabel}</span>`;
        const status = document.createElement("div");
        status.className = "small text-info mt-2 solution-generation-progress";
        status.setAttribute("role", "status");
        status.setAttribute("aria-live", "polite");
        status.textContent = statusLabel;
        form.insertAdjacentElement("afterend", status);
      } else {
        button.textContent = buttonLabel;
      }
    });
  };

  document.querySelectorAll('form[action$="/copilot/"]').forEach((form) => {
    attachSubmitGuard(form, {buttonLabel: "Analyse läuft …"});
  });

  document
    .querySelectorAll('form[action*="/solution-generation/start/"]')
    .forEach((form) => {
      attachSubmitGuard(form, {
        buttonLabel: "KI-Entwürfe werden erstellt …",
        statusLabel: "KI-Generierung läuft. Das kann einige Sekunden dauern.",
      });
    });
});
