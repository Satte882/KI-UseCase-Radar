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
    prepareTargets();
    focusRequestedStep();
  });
})();
