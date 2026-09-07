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

  function relativeRect(element, containerRect) {
    const rect = element.getBoundingClientRect();
    const left = rect.left - containerRect.left;
    const top = rect.top - containerRect.top;
    return {
      left,
      top,
      right: rect.right - containerRect.left,
      bottom: rect.bottom - containerRect.top,
      width: rect.width,
      height: rect.height,
      cx: left + rect.width / 2,
      cy: top + rect.height / 2,
    };
  }

  function appendArrowHead(svg, ex, ey, ux, uy, color, width) {
    const arrowLength = 10;
    const arrowHalf = 5;
    const baseX = ex - arrowLength * ux;
    const baseY = ey - arrowLength * uy;
    const px = -uy;
    const py = ux;
    const leftX = baseX + px * arrowHalf;
    const leftY = baseY + py * arrowHalf;
    const rightX = baseX - px * arrowHalf;
    const rightY = baseY - py * arrowHalf;

    svg.append(
      svgElement("path", {
        d: `M ${leftX} ${leftY} L ${ex} ${ey} L ${rightX} ${rightY}`,
        fill: "none",
        stroke: color,
        "stroke-width": width,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        "vector-effect": "non-scaling-stroke",
      }),
    );

    return { baseX, baseY };
  }

  function drawLineArrowPoints(svg, sx, sy, ex, ey, color = "#8ea4b5", width = 2.1) {
    const dx = ex - sx;
    const dy = ey - sy;
    const length = Math.hypot(dx, dy);
    if (length < 12) return;

    const ux = dx / length;
    const uy = dy / length;
    const { baseX, baseY } = appendArrowHead(svg, ex, ey, ux, uy, color, width);

    svg.prepend(
      svgElement("line", {
        x1: sx,
        y1: sy,
        x2: baseX,
        y2: baseY,
        stroke: color,
        "stroke-width": width,
        "stroke-linecap": "round",
        "vector-effect": "non-scaling-stroke",
      }),
    );
  }

  function drawCubicLine(svg, points, color = "#8ea4b5", width = 2.1) {
    svg.append(
      svgElement("path", {
        d: `M ${points.sx} ${points.sy} C ${points.c1x} ${points.c1y}, ${points.c2x} ${points.c2y}, ${points.ex} ${points.ey}`,
        fill: "none",
        stroke: color,
        "stroke-width": width,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        "vector-effect": "non-scaling-stroke",
      }),
    );
  }

  function drawCubicArrow(svg, points, color = "#8ea4b5", width = 2.1) {
    const dx = points.ex - points.c2x;
    const dy = points.ey - points.c2y;
    const length = Math.hypot(dx, dy);
    if (length < 1) return;

    const ux = dx / length;
    const uy = dy / length;
    const { baseX, baseY } = appendArrowHead(svg, points.ex, points.ey, ux, uy, color, width);

    svg.prepend(
      svgElement("path", {
        d: `M ${points.sx} ${points.sy} C ${points.c1x} ${points.c1y}, ${points.c2x} ${points.c2y}, ${baseX} ${baseY}`,
        fill: "none",
        stroke: color,
        "stroke-width": width,
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        "vector-effect": "non-scaling-stroke",
      }),
    );
  }

  function drawArrow(svg, containerRect, from, to, color = "#8ea4b5", width = 2.1) {
    const startRect = relativeRect(from, containerRect);
    const endRect = relativeRect(to, containerRect);
    drawLineArrowPoints(
      svg,
      startRect.right + 6,
      startRect.cy,
      endRect.left - 8,
      endRect.cy,
      color,
      width,
    );
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

  function drawDataGraphConnectors() {
    const container = document.querySelector("#sci-slide-2 .sci-data-graph");
    if (!container || container.closest(".sci-slide-shell")?.hidden) return;

    const sources = Array.from(container.querySelectorAll(".sci-source"));
    const join = container.querySelector(".sci-icon-circle.join");
    const outcome = container.querySelector(".sci-outcome .sci-icon-circle.amber");
    if (sources.length !== 4 || !join || !outcome) return;

    const layer = createConnectorLayer(container, "sci-data-connectors");
    if (!layer) return;

    const [call, campaign, customer, trip] = sources.map((source) => relativeRect(source, layer.rect));
    const joinRect = relativeRect(join, layer.rect);
    const outcomeRect = relativeRect(outcome, layer.rect);
    const color = "#7891a4";
    const width = 2.15;

    // Reference topology: Call + Kunde merge into one middle route.
    const mergeX = call.right + Math.max(34, (campaign.left - call.right) * 0.48);
    const mergeY = joinRect.cy;

    drawCubicLine(
      layer.svg,
      {
        sx: call.right + 6,
        sy: call.cy,
        c1x: call.right + 34,
        c1y: call.cy,
        c2x: mergeX - 34,
        c2y: mergeY,
        ex: mergeX,
        ey: mergeY,
      },
      color,
      width,
    );

    drawCubicLine(
      layer.svg,
      {
        sx: customer.right + 6,
        sy: customer.cy,
        c1x: customer.right + 34,
        c1y: customer.cy,
        c2x: mergeX - 34,
        c2y: mergeY,
        ex: mergeX,
        ey: mergeY,
      },
      color,
      width,
    );

    drawLineArrowPoints(
      layer.svg,
      mergeX,
      mergeY,
      joinRect.left - 10,
      joinRect.cy,
      color,
      width,
    );

    // Kampagne and Reise remain independent curved inputs into the join node.
    const upperTargetY = joinRect.cy - joinRect.height * 0.18;
    const lowerTargetY = joinRect.cy + joinRect.height * 0.18;

    drawCubicArrow(
      layer.svg,
      {
        sx: campaign.right + 6,
        sy: campaign.cy,
        c1x: campaign.right + 34,
        c1y: campaign.cy,
        c2x: joinRect.left - 46,
        c2y: upperTargetY,
        ex: joinRect.left - 10,
        ey: upperTargetY,
      },
      color,
      width,
    );

    drawCubicArrow(
      layer.svg,
      {
        sx: trip.right + 6,
        sy: trip.cy,
        c1x: trip.right + 34,
        c1y: trip.cy,
        c2x: joinRect.left - 46,
        c2y: lowerTargetY,
        ex: joinRect.left - 10,
        ey: lowerTargetY,
      },
      color,
      width,
    );

    drawLineArrowPoints(
      layer.svg,
      joinRect.right + 12,
      joinRect.cy,
      outcomeRect.left - 12,
      outcomeRect.cy,
      "#5d7f98",
      2.25,
    );
  }

  function drawStageGateConnectors() {
    const container = document.querySelector("#sci-slide-4 .sci-gates");
    if (!container || container.closest(".sci-slide-shell")?.hidden) return;

    const decisions = Array.from(container.querySelectorAll(".sci-decision"));
    const numbers = Array.from(container.querySelectorAll(".sci-gate-num"));
    const stages = Array.from(container.querySelectorAll(".sci-gate-stage"));
    const finalIcon = container.querySelector(".sci-final .sci-icon-circle.amber");
    if (decisions.length !== 2 || numbers.length !== 3 || stages.length !== 3 || !finalIcon) return;

    const layer = createConnectorLayer(container, "sci-gate-connectors");
    if (!layer) return;

    decisions.forEach((decision, index) => {
      const diamond = decision.querySelector(".sci-diamond");
      const stop = decision.querySelector(".sci-stop");
      const nextNumber = numbers[index + 1];
      if (!diamond || !stop || !nextNumber) return;

      const diamondRect = relativeRect(diamond, layer.rect);
      const nextRect = relativeRect(nextNumber, layer.rect);
      const stopRect = relativeRect(stop, layer.rect);

      drawLineArrowPoints(
        layer.svg,
        diamondRect.right + 7,
        diamondRect.cy,
        nextRect.left - 9,
        nextRect.cy,
        "#0b6ea6",
        2.2,
      );

      drawLineArrowPoints(
        layer.svg,
        diamondRect.cx,
        diamondRect.bottom + 6,
        diamondRect.cx,
        stopRect.top - 7,
        "#6b8598",
        2.0,
      );
    });

    const stageThreeRect = relativeRect(stages[2], layer.rect);
    const finalRect = relativeRect(finalIcon, layer.rect);
    drawLineArrowPoints(
      layer.svg,
      stageThreeRect.right + 8,
      finalRect.cy,
      finalRect.left - 10,
      finalRect.cy,
      "#0b6ea6",
      2.2,
    );
  }

  function drawActiveConnectors() {
    drawSequentialConnectors(
      "#sci-slide-1 .sci-flow",
      ".sci-flow-node",
      "sci-flow-connectors",
      (index) => (index === 5 ? "#d69200" : index === 2 ? "#0b6ea6" : "#8ea4b5"),
    );

    drawDataGraphConnectors();

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

    drawStageGateConnectors();
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
  if (document.fonts?.ready) document.fonts.ready.then(scheduleConnectorDraw);

  const hashMatch = window.location.hash.match(/^#slide-([1-4])$/);
  showSlide(hashMatch ? Number(hashMatch[1]) - 1 : 0, false);
})();
