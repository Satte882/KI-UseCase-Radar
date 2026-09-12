(() => {
  function revealHashTarget() {
    if (!window.location.hash || window.location.hash === "#") return;

    let targetId;
    try {
      targetId = decodeURIComponent(window.location.hash.slice(1));
    } catch (_error) {
      targetId = window.location.hash.slice(1);
    }

    const target = document.getElementById(targetId);
    if (!target) return;

    if (target.matches("details")) target.open = true;
    let disclosure = target.closest("details");
    while (disclosure) {
      disclosure.open = true;
      disclosure = disclosure.parentElement?.closest("details") || null;
    }

    const focusTarget = target.matches("details")
      ? target.querySelector(":scope > summary")
      : target;
    if (focusTarget && typeof focusTarget.focus === "function") {
      if (focusTarget.tabIndex < 0 && !focusTarget.matches("summary")) {
        focusTarget.setAttribute("tabindex", "-1");
      }
      focusTarget.focus({ preventScroll: true });
    }
    target.scrollIntoView({ block: "start" });
  }

  window.addEventListener("DOMContentLoaded", revealHashTarget);
  window.addEventListener("hashchange", revealHashTarget);
})();
