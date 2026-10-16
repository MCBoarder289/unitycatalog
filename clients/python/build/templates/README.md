# Custom Python generator templates

`model_generic.mustache` in this directory is a copy of the stock OpenAPI Generator
7.9.0 `python/model_generic.mustache` template with one change: the four `{{#allVars}}`
loops used to render `__properties`, the `to_dict()` nested-object/nullable overrides,
and the `from_dict()` field construction are switched to `{{#vars}}`.

## Why

`api/delta.yaml` models polymorphic requirement/update payloads
(`DeltaTableRequirement`/`DeltaTableUpdate` and their subtypes) using `allOf` +
`discriminator`, with each subtype redeclaring the discriminator property and adding
its own fields as siblings of `allOf`. For these generated Python models, OpenAPI
Generator 7.9.0's codegen IR populates `vars` (the subtype's own declared fields,
including the redeclared discriminator) correctly, but `allVars` for the same model
collapses to just the discriminator field, silently dropping every other field
(e.g. `uuid` on `DeltaAssertTableUUID`, `updates` on `DeltaSetPropertiesUpdate`).
Since the stock template uses `allVars` for `__properties`/`to_dict`/`from_dict`,
required subtype fields never round-trip through generated (de)serialization.

The equivalent Java-side generation is unaffected (Java's codegen computes subtype
fields correctly), so this is a Python-generator-specific defect, not a spec problem.
Restructuring the spec to the conventional two-item `allOf` form (`$ref` + inline
`type: object`) does fix Python's `allVars`, but breaks Java compilation (codegen
emits an incompatible enum-typed override for the discriminator property), so a spec
change is not viable without touching both client languages. Hence this narrow,
Python-generation-only template override instead.

This override is scoped to the `unitycatalog.delta` Python package generation only
(wired via `templateDir` on that `OpenApiSpec` in `build.sbt`); it does not affect the
native `unitycatalog.client` Python generation or the Java client.

## Maintenance

Re-diff this file against the stock `python/model_generic.mustache` template whenever
the pinned `sbt-openapi-generator`/`openapi-generator` version changes, and re-apply
the same four `allVars` -> `vars` substitutions (search for `{{#allVars}}`/`{{/allVars}}`)
if the stock template has otherwise changed. Re-run `build/sbt pythonClient/generate`
and the `unitycatalog.delta` tests afterward to confirm the override still applies
and the generated subtype models still include all declared fields.
