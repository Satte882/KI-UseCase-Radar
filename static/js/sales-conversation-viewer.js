(() => {
  "use strict";

  const deck = document.querySelector(".sci-deck");
  if (!deck) return;

  const slides = Array.from(deck.querySelectorAll(".sci-slide-shell"));
  if (!slides.length) return;

  const labels = ["Business-Frage", "Datenbasis", "Pilot-Architektur", "Entscheidung"];
  const backLink = document.querySelector(".sci-back-link");

  const stage = document.createElement("div");
  stage.className = "sci-stage";
  slides[0].before(stage);
  slides.forEach((slide) => stage.append(slide));

  const nav = document.createElement("nav");
  nav.className = "sci-slide-nav";
  nav.setAttribute("aria-label", "Foliennavigation");

  const navButtons = labels
    .map(
      (label, index) => `
        <button class="sci-nav-button" type="button" data-sci-slide="${index}" aria-label="Folie ${index + 1}: ${label}">
          <span class="sci-nav-number">${String(index + 1).padStart(2, "0")}</span>
          <span class="sci-nav-label">${label}</span>
        </button>`,
    )
    .join("");

  nav.innerHTML = `
    <div class="sci-nav-eyebrow">Case Study</div>
    <div class="sci-nav-title">Sales Conversation Intelligence</div>
    <div class="sci-nav-list">${navButtons}</div>
    <div class="sci-nav-meta">
      <a class="sci-nav-home" href="${backLink ? backLink.href : "/demo/"}">← Zur Übersicht</a>
      <div class="sci-nav-controls" aria-label="Vor und zurück">
        <button class="sci-nav-control sci-nav-prev" type="button" aria-label="Vorherige Folie">←</button>
        <button class="sci-nav-control sci-nav-next" type="button" aria-label="Nächste Folie">→</button>
      </div>
      <div class="sci-nav-progress" aria-live="polite"></div>
    </div>`;

  deck.prepend(nav);

  const buttons = Array.from(nav.querySelectorAll("[data-sci-slide]"));
  const prevButton = nav.querySelector(".sci-nav-prev");
  const nextButton = nav.querySelector(".sci-nav-next");
  const progress = nav.querySelector(".sci-nav-progress");

  let current = 0;
  let resizeFrame = null;

  function svgElement(name, attrs = {}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, value));
    return element;
  }

  function createConnectorLayer(container, className) {
    const existing = container.querySelector(`:scope > .${className}`);
    if (existing) existing.remove();

    const rect = container.getBoundingClientRect();
    if (!rect.width || !rect.height) return null;

    const svg = svgElement("svg", {
      class: `sci-connector-layer ${className}`,
      viewBox: `0 0 ${rect.width} ${rect.height}`,
      preserveAspectRatio: "none",
      "aria-hidden": "true",
    });
    container.prepend(svg);
    return { svg, rect };
  }

  function drawArrow(svg, containerRect, from, to, color = "#8ea4b5", width = 2.1) {
    const startRect = from.getBoundingClientRect();
    const endRect = to.getBoundingClientRect();

    const sx = startRect.right - containerRect.left + 6;
    const sy = startRect.top + startRect.height / 2 - containerRect.top;
    const ex = endRect.left - containerRect.left - 8;
    const ey = endRect.top + endRect.height / 2 - containerRect.top;

    const dx = ex - sx;
    const dy = ey - sy;
    const length = Math.hypot(dx, dy);
    if (length < 12) return;

    const ux = dx / length;
    const uy = dy / length;
    const arrowLength = 10;
    const arrowHalf = 5;
    const lineEndX = ex - arrowLength * ux;
    const lineEndY = ey - arrowLength * uy;

    const line = svgElement("line", {
      x1: sx,
      y1: sy,
      x2: lineEndX,
      y2: lineEndY,
      stroke: color,
      "stroke-width": width,
      "stroke-linecap": "round",
      "vector-effect": "non-scaling-stroke",
    });

    const baseX = ex - arrowLength * ux;
    const baseY = ey - arrowLength * uy;
    const px = -uy;
    const py = ux;
    const leftX = baseX + px * arrowHalf;
    const leftY = baseY + py * arrowHalf;
    const rightX = baseX - px * arrowHalf;
    const rightY = baseY - py * arrowHalf;

    const head = svgElement("path", {
      d: `M ${leftX} ${leftY} L ${ex} ${ey} L ${rightX} ${rightY}`,
      fill: "none",
      stroke: color,
      "stroke-width": width,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "vector-effect": "non-scaling-stroke",
    });

    svg.append(line, head);
  }

  function drawSequentialConnectors(containerSelector, nodeSelector, layerClass, colorForPair) {
    const container = document.querySelector(containerSelector);
    if (!container || container.closest(".sci-slide-shell")?.hidden) return;

    const nodes = Array.from(container.querySelectorAll(nodeSelector));
    if (nodes.length < 2) return;

    const layer = createConnectorLayer(container, layerClass);
    if (!layer) return;

    nodes.slice(0, -1).forEach((node, index) => {
      const color = colorForPair ? colorForPair(index, nodes[index + 1]) : "#8ea4b5";
      drawArrow(layer.svg, layer.rect, node, nodes[index + 1], color, 2.15);
    });
  }

  function drawDataConnectors() {
    const container = document.querySelector("#sci-slide-2 .sci-data-graph");
    if (!container || container.closest(".sci-slide-shell")?.hidden) return;

    const sources = container.querySelector(".sci-source-grid");
    const join = container.querySelector(".sci-icon-circle.join");
    const outcome = container.querySelector(".sci-outcome .sci-icon-circle.amber");
    if (!sources || !join || !outcome) return;

    const layer = createConnectorLayer(container, "sci-data-connectors");
    if (!layer) return;
    drawArrow(layer.svg, layer.rect, sources, join, "#8ea4b5", 2.15);
    drawArrow(layer.svg, layer.rect, join, outcome, "#7790a3", 2.2);
  }

  function drawActiveConnectors() {
    drawSequentialConnectors(
      "#sci-slide-1 .sci-flow",
      ".sci-flow-node",
      "sci-flow-connectors",
      (index) => (index === 5 ? "#d69200" : index === 2 ? "#0b6ea6" : "#8ea4b5"),
    );

    drawSequentialConnectors(
      "#sci-slide-3 .sci-architecture",
      ".sci-arch-step .sci-icon-circle",
      "sci-architecture-connectors",
      (_index, nextNode) => {
        if (nextNode.classList.contains("amber")) return "#d69200";
        if (nextNode.classList.contains("blue")) return "#0b6ea6";
        return "#8ea4b5";
      },
    );

    drawDataConnectors();
  }

  function scheduleConnectorDraw() {
    if (resizeFrame) cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      requestAnimationFrame(drawActiveConnectors);
    });
  }

  function showSlide(index, updateHash = true) {
    const next = Math.max(0, Math.min(slides.length - 1, index));
    current = next;

    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.hidden = !active;
      slide.classList.toggle("is-active", active);
    });

    buttons.forEach((button, buttonIndex) => {
      const active = buttonIndex === current;
      button.classList.toggle("is-active", active);
      if (active) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });

    prevButton.disabled = current === 0;
    nextButton.disabled = current === slides.length - 1;
    progress.textContent = `${current + 1} / ${slides.length}`;

    if (updateHash) history.replaceState(null, "", `#slide-${current + 1}`);
    scheduleConnectorDraw();
  }

  function step(delta) {
    showSlide(current + delta);
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => showSlide(Number(button.dataset.sciSlide)));
  });
  prevButton.addEventListener("click", () => step(-1));
  nextButton.addEventListener("click", () => step(1));

  window.addEventListener("keydown", (event) => {
    const tagName = event.target?.tagName;
    if (tagName === "INPUT" || tagName === "TEXTAREA" || tagName === "SELECT") return;

    if (["ArrowRight", "PageDown", " "].includes(event.key)) {
      event.preventDefault();
      step(1);
      return;
    }
    if (["ArrowLeft", "PageUp"].includes(event.key)) {
      event.preventDefault();
      step(-1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      showSlide(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      showSlide(slides.length - 1);
      return;
    }
    if (/^[1-4]$/.test(event.key)) {
      event.preventDefault();
      showSlide(Number(event.key) - 1);
    }
  });

  window.addEventListener("resize", scheduleConnectorDraw, { passive: true });

  const hashMatch = window.location.hash.match(/^#slide-([1-4])$/);
  showSlide(hashMatch ? Number(hashMatch[1]) - 1 : 0, false);
})();