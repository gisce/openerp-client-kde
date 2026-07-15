# GISCE ERP Qt Client functionality matrix

This PR must be treated as the start of a new GISCE-owned Qt6 ERP client, not
as the target architecture for the legacy `Koo/` codebase.

The implementation package is still named `koo2` while the branch is in draft,
but the product-facing name should be `GISCE ERP Qt Client` unless the project
settles on a different final name.

Status values:

- `covered`: implemented and covered by automated tests in this PR.
- `partial`: initial implementation exists, but it is not enough to replace the
  current Koo behaviour.
- `missing`: required before the new client can be considered a functional
  replacement.

| ID | Capability | Legacy Koo behaviour to preserve | New client status | Test target |
| --- | --- | --- | --- | --- |
| F01 | Authentication and session bootstrap | Connect to an ERP server, authenticate the user, keep session context and surface authentication errors. | partial | `tests/koo2/infrastructure/test_erppeek_client.py`, `tests/koo2/infrastructure/test_restapi_client.py`, `tests/koo2/ui/test_login_dialog.py` |
| F02 | QGIS-oriented launch contract | Allow QGIS 4 / Qt6 integrations to launch the new client independently from legacy Koo versions. | missing | Launch contract test once the qgisce integration entry point is agreed. |
| F03 | Menu and action loading | Load ERP menus/actions and open the requested model, wizard, report or URL action. | covered | `tests/koo2/core/test_action_service.py` |
| F04 | Form view parsing | Parse `fields_view_get` XML forms with groups, notebooks, labels, separators, buttons, modifiers and field metadata. | partial | `tests/koo2/core/test_view_parser.py` |
| F05 | Tree/list view parsing | Parse list views, preserve column order, metadata, visibility and read-only state. | partial | `tests/koo2/core/test_view_parser.py` |
| F06 | Search view and filters | Render ERP search views, domains, contexts, saved filters and quick filters. | missing | Search parser and search model tests. |
| F07 | Field widgets | Render and edit scalar fields, selections, dates, booleans, relational fields, binary/image/url/html fields and required/read-only/invisible state. | partial | `tests/koo2/ui/test_widgets_factory.py` |
| F08 | Relational field workflows | Support many2one lookup/create/open, one2many and many2many embedded lists/forms and inline commands. | missing | Repository-backed relational widget tests. |
| F09 | Record lifecycle | Create, read, update, delete, duplicate, discard changes, reload and detect dirty records. | covered | `tests/koo2/core/test_record.py`, `tests/koo2/core/test_record_lifecycle_service.py` |
| F10 | Button, object and workflow actions | Execute object buttons, workflow transitions, action buttons and confirmation prompts with context. | missing | Action executor tests. |
| F11 | Wizards | Open transient models, run multi-step wizard flows and apply returned actions. | missing | Wizard controller tests. |
| F12 | Reports and print actions | Execute report actions, download/open generated files and surface report errors. | missing | Report service tests with mocked RPC responses. |
| F13 | Attachments | List, upload, download and delete record attachments. | missing | Attachment repository and UI controller tests. |
| F14 | Import/export | Export visible/search result data and import structured files where current Koo exposes that workflow. | missing | Import/export service tests. |
| F15 | Preferences, shortcuts and saved state | Persist user preferences, shortcuts, window state, view options and recent connections. | missing | Settings adapter tests. |
| F16 | Navigation shell | Provide main window, tabs/windows, breadcrumbs, refresh, back/forward and close behaviours expected from Koo users. | missing | Main shell controller tests. |
| F17 | Error handling and notifications | Show user-facing RPC, validation, access, network and unexpected errors without crashing. | missing | Error mapper and UI notification tests. |
| F18 | Theme alignment with webclient | Use GISCE visual language aligned with the ERP webclient, not the old Koo look and feel. | partial | `tests/koo2/ui/test_theme.py` plus visual checks when UI is runnable. |
| F19 | Legacy independence | The new client core, infrastructure and UI must not import or depend on `Koo/` modules. | covered | `tests/test_new_client_contract.py` |

Before this PR leaves draft, every `missing` row must either become covered by
implementation/tests or be explicitly split into a linked follow-up PR/task.
