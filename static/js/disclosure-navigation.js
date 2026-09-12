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

  function setActiveLocalWorkTarget(targetId) {
    document.querySelectorAll(".cr-local-work-status__item[data-work-target]").forEach((item) => {
      const isActive = item.dataset.workTarget === targetId;
      item.classList.toggle("active", isActive);
      if (isActive) {
        item.setAttribute("aria-current", "location");
      } else {
        item.removeAttribute("aria-current");
      }
    });
  }

  function updateVisibleLocalWorkTarget() {
    const items = Array.from(
      document.querySelectorAll(".cr-local-work-status__item[data-work-target]"),
    );
    if (!items.length) return;

    const targets = items
      .map((item) => document.getElementById(item.dataset.workTarget))
      .filter(Boolean);
    if (!targets.length) return;

    const referenceLine = Math.min(180, window.innerHeight * 0.25);
    let candidate = targets[0];
    for (const target of targets) {
      const rect = target.getBoundingClientRect();
      if (rect.top <= referenceLine) {
        candidate = target;
        continue;
      }
      if (candidate === targets[0] && targets[0].getBoundingClientRect().top > referenceLine) {
        candidate = target;
      }
      break;
    }
    setActiveLocalWorkTarget(candidate.id);
  }

  function bindLocalWorkStatus() {
    if (!document.querySelector(".cr-local-work-status")) return;

    let scheduled = false;
    const scheduleUpdate = () => {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(() => {
        scheduled = false;
        updateVisibleLocalWorkTarget();
      });
    };

    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate);
    scheduleUpdate();
  }

  window.addEventListener("DOMContentLoaded", () => {
    revealHashTarget();
    bindLocalWorkStatus();
  });
  window.addEventListener("hashchange", () => {
    revealHashTarget();
    updateVisibleLocalWorkTarget();
  });
})();
