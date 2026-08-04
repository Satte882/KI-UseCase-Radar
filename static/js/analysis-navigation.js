(() => {
  const stepTargets = {
    value_stream: {
      id: "value-stream",
      selector: ".architecture-summary-grid",
    },
    focus: {
      id: "fokus-priorisierung",
      selector: ".architecture-summary-grid + .decision-panel",
    },
    process: {
      id: "prozessanalyse",
      selector: "#prozessdetails + .app-card",
    },
    solution: {
      id: "loesungsoptionen",
      selector: "#loesungsoptionen",
    },
  };

  function elevateMethodologyLabels() {
    const marker = " Methodik: ";

    document.querySelectorAll(".card-header .small.text-muted").forEach((description) => {
      const text = description.textContent.trim();
      const markerIndex = text.indexOf(marker);
      if (markerIndex === -1) return;

      const heading = description.parentElement?.querySelector(":scope > strong");
      if (!heading || heading.nextElementSibling?.dataset.methodologyLabel === "true") return;

      const summary = text.slice(0, markerIndex);
      const methodology = text.slice(markerIndex + marker.length).replace(/\.$/, "");
      description.textContent = summary;

      const label = document.createElement("span");
      label.className = "small text-muted fw-normal ms-1";
      label.dataset.methodologyLabel = "true";
      label.textContent = `(${methodology})`;
      heading.insertAdjacentElement("afterend", label);
    });
  }

  function prepareTargets() {
    Object.values(stepTargets).forEach(({ id, selector }) => {
      const target = document.querySelector(selector);
      if (!target) return;
      if (!document.getElementById(id)) target.id = id;
    });
  }

  function focusRequestedStep() {
    const requestedStep = new URLSearchParams(window.location.search).get("analysis_step");
    const definition = stepTargets[requestedStep];
    if (!definition) return;

    const target = document.getElementById(definition.id);
    if (!target) return;

    if (!target.hasAttribute("tabindex")) target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
    target.scrollIntoView({ block: "start" });
  }

  document.addEventListener("DOMContentLoaded", () => {
    elevateMethodologyLabels();
    prepareTargets();
    focusRequestedStep();
  });
})();
