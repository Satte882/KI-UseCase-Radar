document.addEventListener("DOMContentLoaded", () => {
  const forms = document.querySelectorAll('form[action$="/copilot/"]');

  forms.forEach((form) => {
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
      button.textContent = "Analyse läuft …";
    });
  });
});
