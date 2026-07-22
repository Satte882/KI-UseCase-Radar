(() => {
  "use strict";

  const EXAMPLES = {
    title: "(z. B. automatische Prüfung von Eingangsrechnungen)",
    name: "(z. B. Beschaffung bis Zahlung)",
    capability: "(z. B. Source-to-Pay oder Accounts Payable)",
    business_capability: "(z. B. Supplier Sourcing oder Customer Service Management)",
    process_area: "(z. B. Eingangsrechnungsprüfung)",
    focus_rationale: "(z. B. hoher wirtschaftlicher Hebel, belastbare Baseline und zugängliche Daten)",
    summary: "(z. B. Rechnungen werden heute manuell mit Bestellung und Wareneingang abgeglichen)",
    description: "(z. B. kurzer fachlicher Kontext und erwartetes Ergebnis)",
    problem_statement: "(z. B. die manuelle Prüfung dauert elf Minuten je Rechnung und verursacht Rückfragen)",
    affected_process: "(z. B. Eingangsrechnung prüfen und freigeben)",
    target_users: "(z. B. Mitarbeitende in Buchhaltung und Einkauf)",
    intended_users: "(z. B. Mitarbeitende in Buchhaltung und Einkauf)",
    intended_purpose: "(z. B. Abweichungen erkennen und zur manuellen Prüfung vorlegen)",
    source_systems: "(z. B. ERP, E-Mail-Postfach und Dokumentenablage)",
    systems: "(z. B. ERP, E-Mail-Postfach und Dokumentenablage)",
    system_landscape: "(z. B. ERP bleibt führend; Prüfservice ergänzt den Prozess und schreibt Status zurück)",
    documents: "(z. B. Rechnung, Bestellung und Wareneingangsbeleg)",
    data_sources: "(z. B. Rechnung, Bestellung und Wareneingangsdaten aus dem ERP)",
    data_requirements: "(z. B. Rechnungsnummer, Bestellposition, Menge und Preis)",
    data_flows: "(z. B. PDF aus Postfach → Extraktion → ERP-Abgleich → Prüfentscheidung)",
    interface_description: "(z. B. Rechnungsdaten per API aus dem ERP lesen)",
    integration_contracts: "(z. B. ERP-Team verantwortet API; Fachbereich verantwortet Freigaberegeln)",
    architecture_artifacts_url: "(z. B. https://confluence.example/architecture/invoice-check)",
    expected_benefit: "(z. B. Prüfzeit von elf auf fünf Minuten je Rechnung senken)",
    metric_name: "(z. B. durchschnittliche Prüfzeit je Rechnung)",
    metric_unit: "(z. B. Minuten je Rechnung)",
    metric_baseline: "(z. B. 11)",
    metric_target: "(z. B. 5)",
    metric_actual: "(z. B. 4,8)",
    metric_measurement_method: "(z. B. Mittelwert aus 100 Rechnungen über vier Wochen)",
    baseline: "(z. B. derzeit elf Minuten Prüfzeit je Rechnung)",
    baseline_metrics: "(z. B. elf Minuten je Rechnung und fünf Rückfragen pro Woche)",
    success_criterion: "(z. B. mindestens 40 Prozent kürzere Prüfzeit)",
    realized_result: "(z. B. durchschnittlich 4,8 Minuten je Rechnung)",
    provider: "(z. B. Microsoft)",
    product_name: "(z. B. Azure Document Intelligence)",
    model_name: "(z. B. internes Klassifikationsmodell v1)",
    one_time_cost: "(z. B. 15000)",
    recurring_cost: "(z. B. 800 pro Monat)",
    scope: "(z. B. vom Rechnungseingang bis zur Zahlungsfreigabe)",
    strategic_objective: "(z. B. Durchlaufzeit senken und Entscheidungen nachvollziehbar machen)",
    stakeholders: "(z. B. Buchhaltung, Einkauf, Fachbereich und IT)",
    constraints: "(z. B. das ERP bleibt das führende System)",
    pain_points: "(z. B. manuelle Suche, Medienbrüche und wiederholte Rückfragen)",
    handoffs: "(z. B. Buchhaltung übergibt Abweichungen an den Einkauf)",
    bottlenecks: "(z. B. fehlende Bestellnummern verursachen Wartezeiten)",
    exceptions: "(z. B. Teilrechnungen und abweichende Mengeneinheiten)",
    target_state_principles: "(z. B. Standardfälle automatisieren, Ausnahmen manuell prüfen)",
    application_impact: "(z. B. Erweiterung des bestehenden Beschaffungsportals)",
    integration_impact: "(z. B. lesender Zugriff auf Bestell- und Wareneingangsdaten)",
    technology_constraints: "(z. B. Betrieb ausschließlich in der bestehenden Azure-Umgebung)",
    risks: "(z. B. unvollständige Stammdaten können zu falschen Zuordnungen führen)",
    architecture_fit: "(z. B. nutzt bestehende Identitäts-, Logging- und Betriebsstandards)",
    human_oversight: "(z. B. Abweichungen über zehn Prozent werden manuell freigegeben)",
    support_responsibility: "(z. B. fachlich Buchhaltung, technisch IT-Betrieb)",
    rationale: "(z. B. hoher Nutzen bei tragfähiger Datenlage und beherrschbaren Risiken)",
    conditions: "(z. B. Vier-Augen-Prinzip und Nachmessung nach 60 Tagen)",
    trigger: "(z. B. eine neue Rechnung geht im zentralen Postfach ein)",
    outcome: "(z. B. die Rechnung ist geprüft, verbucht und zur Zahlung freigegeben)",
    acceptance_criteria: "(z. B. 95 Prozent der Standardfälle werden korrekt erkannt)",
    in_scope: "(z. B. PDF-Rechnungen mit vorhandener Bestellnummer)",
    out_of_scope: "(z. B. handschriftliche Belege und Rechnungen ohne Bestellung)",
    dependencies: "(z. B. vollständige Lieferanten- und Bestellstammdaten)",
  };

  const PLACEHOLDER_TYPES = new Set(["text", "email", "url", "tel", "number", "search"]);
  const STATE_CLASSES = [
    "field-guidance-required-empty",
    "field-guidance-optional-empty",
    "field-guidance-filled",
  ];

  function fieldName(control) {
    const rawName = control.name || control.id || "";
    const finalPart = rawName.split("-").pop() || rawName;
    return finalPart.replace(/^id_/, "");
  }

  function labelText(control) {
    if (!control.id) {
      return "diesem Feld";
    }
    const label = document.querySelector(`label[for="${control.id}"]`);
    if (!label) {
      return "diesem Feld";
    }
    return label.textContent.replace(/\s*\*\s*$/, "").trim() || "diesem Feld";
  }

  function supportsPlaceholder(control) {
    if (control instanceof HTMLTextAreaElement) {
      return true;
    }
    return control instanceof HTMLInputElement && PLACEHOLDER_TYPES.has(control.type);
  }

  function addExample(control) {
    if (!supportsPlaceholder(control) || control.hasAttribute("placeholder")) {
      return;
    }
    const name = fieldName(control);
    control.placeholder = EXAMPLES[name] || `(z. B. kurze konkrete Angabe zu „${labelText(control)}“)`;
  }

  function isEmpty(control) {
    if (control instanceof HTMLSelectElement && control.multiple) {
      return control.selectedOptions.length === 0;
    }
    return String(control.value || "").trim() === "";
  }

  function isRequired(control) {
    const fieldWrapper = control.closest("[id^='field-']");
    return (
      control.required ||
      control.getAttribute("aria-required") === "true" ||
      Boolean(fieldWrapper && fieldWrapper.classList.contains("field-attention"))
    );
  }

  function updateState(control) {
    control.classList.remove(...STATE_CLASSES);
    if (!isEmpty(control)) {
      control.classList.add("field-guidance-filled");
      return;
    }
    control.classList.add(
      isRequired(control) ? "field-guidance-required-empty" : "field-guidance-optional-empty"
    );
  }

  function isEligible(control) {
    if (control.disabled || control.readOnly) {
      return false;
    }
    if (control instanceof HTMLInputElement) {
      return !["hidden", "checkbox", "radio", "file", "submit", "button", "reset", "password"].includes(
        control.type
      );
    }
    return control instanceof HTMLTextAreaElement || control instanceof HTMLSelectElement;
  }

  function initializeForm(form) {
    if (form.method.toLowerCase() !== "post" || form.classList.contains("form-guidance-ignore")) {
      return;
    }
    const controls = form.querySelectorAll(".form-control, .form-select");
    controls.forEach((control) => {
      if (!isEligible(control)) {
        return;
      }
      addExample(control);
      updateState(control);
      control.addEventListener("input", () => updateState(control));
      control.addEventListener("change", () => updateState(control));
    });
  }

  function initialize() {
    document.querySelectorAll("form").forEach(initializeForm);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
