const updateDisclosureLabel = (details, closedLabel, openLabel) => {
  const summary = details.querySelector(":scope > summary");
  if (!summary) return;
  summary.textContent = details.open ? openLabel : closedLabel;
};

const enhanceFocusCriteria = () => {
  document.querySelectorAll(".kpi-strip").forEach((strip) => {
    if (strip.children.length !== 5) return;
    strip.style.removeProperty("grid-template-columns");
    strip.classList.add("kpi-strip-responsive");
  });
};

const enhanceValueStreamStages = () => {
  document.querySelectorAll(".value-stream-stage").forEach((stage) => {
    if (stage.dataset.layoutEnhanced === "true") return;

    const detailSections = Array.from(
      stage.querySelectorAll(":scope > .stage-facts, :scope > .stage-use-cases"),
    );
    if (!detailSections.length) return;

    const details = document.createElement("details");
    details.className = "architecture-disclosure stage-disclosure";

    const summary = document.createElement("summary");
    details.append(summary);

    detailSections[0].insertAdjacentElement("beforebegin", details);
    detailSections.forEach((section) => details.append(section));

    const closedLabel = "Phasendetails anzeigen";
    const openLabel = "Phasendetails ausblenden";
    details.addEventListener("toggle", () => {
      updateDisclosureLabel(details, closedLabel, openLabel);
    });
    updateDisclosureLabel(details, closedLabel, openLabel);
    stage.dataset.layoutEnhanced = "true";
  });
};

const enhanceProcessArtifacts = () => {
  document.querySelectorAll(".architecture-artifact-grid > section").forEach((section) => {
    if (section.dataset.layoutEnhanced === "true") return;

    const title = section.querySelector(":scope > .section-title");
    const contentLength = section.textContent.trim().length;
    if (!title || contentLength < 180) return;

    const details = document.createElement("details");
    details.className = "architecture-disclosure artifact-disclosure";

    const summary = document.createElement("summary");
    summary.textContent = title.textContent.trim();
    details.append(summary);

    title.remove();
    while (section.firstChild) details.append(section.firstChild);
    section.append(details);
    section.dataset.layoutEnhanced = "true";
  });
};

const enhanceLongSourceLists = () => {
  const processPage = document.querySelector(".architecture-artifact-grid");
  if (!processPage) return;

  document.querySelectorAll(".alert > ul").forEach((list) => {
    if (list.dataset.layoutEnhanced === "true") return;
    if (list.children.length < 3 && list.textContent.trim().length < 240) return;

    const details = document.createElement("details");
    details.className = "architecture-disclosure source-disclosure mt-2";

    const summary = document.createElement("summary");
    details.append(summary);
    list.insertAdjacentElement("beforebegin", details);
    details.append(list);

    const closedLabel = "Quellendetails anzeigen";
    const openLabel = "Quellendetails ausblenden";
    details.addEventListener("toggle", () => {
      updateDisclosureLabel(details, closedLabel, openLabel);
    });
    updateDisclosureLabel(details, closedLabel, openLabel);
    list.dataset.layoutEnhanced = "true";
  });
};

const enhanceArchitectureLayout = () => {
  enhanceFocusCriteria();
  enhanceValueStreamStages();
  enhanceProcessArtifacts();
  enhanceLongSourceLists();
};

document.addEventListener("DOMContentLoaded", enhanceArchitectureLayout);
