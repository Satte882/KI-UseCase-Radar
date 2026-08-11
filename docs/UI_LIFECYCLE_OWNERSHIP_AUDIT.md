# Lifecycle Ownership Audit

Bezug: #295, Parent #286, UI-vNext-Gesamtplan #279.

## Zweck

Dieser Audit trennt echte Lifecycle-Redundanz von fachlich eigenständigen Subworkflows. Eine horizontale Leiste wird nur entfernt oder konsolidiert, wenn Renderer und Datenquelle dieselbe Journey darstellen. Form- und Wizard-Schritte mit eigener Datenquelle bleiben erhalten.

## Kanonische Renderer

- Globaler Legacy-Kontext: `templates/includes/context_topbar.html` berechnet `workflow_steps journey request as workflow` und rendert `journey-progress` inklusive globalem Next-Action-Kontext.
- Lokaler Legacy-Renderer: `templates/includes/journey_stepper.html` berechnet ebenfalls `workflow_steps journey request as workflow`. Treffen beide auf derselben Seite zusammen, ist das eine echte `duplicate-same-source`-Situation.
- Lokaler UI-vNext-Renderer: `templates/includes/lifecycle_rail.html` berechnet dieselbe fachliche Journey, rendert sie jedoch als lokales Work-Object-Primitive mit echten Links und `aria-current`.

## Klassifikation

| Bereich / Template | Datenquelle / lokaler Ablauf | Klasse | Befund / Migration |
| --- | --- | --- | --- |
| Use Case Detail `use_cases/detail.html` | `journey` → `lifecycle_rail.html`; globaler Topbar explizit unterdrückt | `local-only` | Kanonische Referenz aus Gate B. |
| Value Stream Detail `architecture/value_stream_detail.html` | `journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` → `local-only` | Referenzfix in #295: global unterdrücken, lokal auf `lifecycle_rail.html` migrieren. |
| Prozessanalyse Detail `architecture/process_analysis_detail.html` | `build_process_analysis_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren; nicht im Referenzfix vorziehen. |
| Delivery Package Detail `delivery/package_detail.html` | `build_delivery_package_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren. |
| Governance Screening `governance/form.html` | `build_use_case_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren. |
| Governance Review `governance/review_form.html` | `build_use_case_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren. |
| Bewertung `use_cases/assessment_form.html` | `build_use_case_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren. |
| Freigabeentscheidung `use_cases/decision_form.html` | `build_use_case_journey` → globaler Topbar und lokaler `journey_stepper.html` | `duplicate-same-source` | In breitem AP7-Rollout konsolidieren. |
| Wirkung & Betrieb `reporting/outcome_workspace.html` | globaler Lifecycle im speziell behandelten `context_topbar.html`; kein lokaler Journey-Renderer | `global-only` | Kein Doppel-Stepper. Im AP7-Rollout erst migrieren, wenn lokaler Work-Object-Owner definiert ist. |
| Use-Case-Aufnahme `use_cases/intake_wizard.html` | lokale `step_states` des Intake-Wizards | `semantic-subworkflow` | Kein Ersatz für die Makro-Journey; Wizard-Schritte bleiben als eigener, benannter Ablauf erhalten. |
| Accelerator Capture `accelerator/capture_wizard.html` | lokale `step_states` der Capture Session | `semantic-subworkflow` | Eigenständige Erfassungsgranularität; erhalten. |
| Delivery Package Edit `delivery/package_form.html` | `section_rows` / „Sektionsworkflow“ innerhalb des Delivery Packages | `semantic-subworkflow` | Fachlich untergeordneter Sektionsablauf; nicht mit Lifecycle gleichsetzen oder entfernen. |

## Produktive Seiten ohne primären Lifecycle-Consumer

Die folgenden Seiten erhalten im aktuellen View-Kontext keine `journey` und binden keinen Makro-Lifecycle-Renderer ein. Sie erzeugen daher keinen Doppel-Stepper und sind für #295 nur als Negativinventar relevant:

- `architecture/process_analysis_form.html`
- `architecture/process_validation_form.html`
- `architecture/solution_option_compare.html`
- `architecture/solution_option_form.html`
- `architecture/stage_focus_form.html`
- `architecture/stage_form.html`
- `delivery/package_form.html` hinsichtlich Makro-Lifecycle; der Sektionsworkflow bleibt ein echter Subworkflow
- `reviews/form.html`
- `use_cases/form.html`
- `use_cases/second_approval_review.html`
- `accelerator/analysis_detail.html`
- `accelerator/capture_review.html`
- `accelerator/solution_generation_preview.html`
- `accelerator/structured_review.html`

## Ergebnis der Ursachenprüfung

Für den sichtbaren Doppel-Stepper auf dem Value Stream ist die Ursache verifiziert: globaler Topbar und lokaler `journey_stepper.html` verwenden dieselbe `journey`-Instanz und denselben `workflow_steps`-Tag. Es handelt sich nicht um Makro- versus Mikroprozess. Die Konsolidierung entfernt daher keine fachliche Granularität.

Echte Subworkflows wurden separat identifiziert: Intake-Wizard, Accelerator-Capture-Wizard und Delivery-Sektionsworkflow. Sie besitzen eigene Schritt-/Sektionsdaten und dürfen nicht aufgrund optischer Ähnlichkeit mit dem Lifecycle entfernt werden.

## Testinventar vor Markup-Änderung

Bestehende Regressionen, die bei Lifecycle-/Next-Action-Änderungen zu berücksichtigen sind:

- `tests/test_context_topbar.py`
- `tests/test_guided_journey.py`
- `tests/test_issue_40_handover_journey.py`
- `tests/test_issue_41_lifecycle_gate_labels.py`
- `tests/test_issue_51_64_primary_actions.py`
- `tests/test_issue_58_final_journey_order.py`
- `tests/test_issue_58_solution_next_action.py`
- `tests/test_issue_58_value_stream_next_action.py`
- `tests/test_outcome_journey_consistency.py`
- `tests/test_use_case_control_room_ui.py`
- `tests/test_delivery_handover.py`
- `tests/test_issue_49_50_55_delivery_workflow.py`

Bestehende Tests werden nur dort angepasst, wo ein bewusst geänderter Markup-Contract dies erfordert. Fachliche Journey-Builder, Rollen, Gates, URLs und Zustandslogik bleiben unverändert.

## Referenzentscheidung für #295

Der Value Stream übernimmt analog zum Use Case Detail die lokale Ownership:

1. `value_stream_detail` optiert in `ui-control-room` ein und lädt die gemeinsamen Work-Object-Primitives.
2. Der globale `context_topbar.html` rendert für diesen Resolver keinen zweiten Lifecycle und keinen zweiten Next-Action-Kontext.
3. Die lokale Legacy-Leiste wird durch `lifecycle_rail.html` ersetzt.
4. Die kanonische Next Action wird lokal genau einmal als primäre Aktion gerendert; kontextuelle Sekundäraktionen dürfen erhalten bleiben, aber dieselbe Journey-Aktion wird nicht nochmals als Primäraktion dupliziert.
5. Desktop verwendet keine horizontale Lifecycle-Scrollfläche; Tablet/Mobile nutzen die responsive Grid-Darstellung des gemeinsamen Primitives.
6. Nach vollständigem CI-Lauf folgt die visuelle Abnahme an einem fortgeschrittenen und einem blockierten/unvollständigen Value Stream. Erst danach wird das Muster auf die übrigen `duplicate-same-source`-Seiten ausgerollt.
