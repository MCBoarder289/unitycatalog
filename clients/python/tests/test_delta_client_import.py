"""
Regression tests ensuring the generated ``unitycatalog.delta`` package ships a
complete, importable runtime.

``build.sbt`` used to generate delta.yaml with
``globalProperties = Map("apis" -> "", "models" -> "")``, which restricts
OpenAPI Generator to only the ``apis``/``models`` categories and skips
``supportingFiles`` -- the runtime modules (``api_client.py``,
``configuration.py``, ``rest.py``, package ``__init__.py``s, ``py.typed``).
That silently shipped a `unitycatalog.delta` package with no runtime at all:
importing `DeltaTablesApi` failed, and because `models/__init__.py` never
existed, `PythonClientPostBuild.patchDeltaDataTypeModule`'s serde patch
(auto-imported from `models/__init__.py`) was silently skipped too.

These tests run in a subprocess (a fresh Python process, not the one pytest
is running in) to ensure the import doesn't rely on anything already loaded
by another test module, matching how a real downstream caller would import
the package. They require the client to already be installed (run
`sbt pythonClient/generate` then install the package, as in `run-tests.sh`).
"""

import subprocess
import sys


def _run(code: str) -> None:
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"subprocess failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


class TestDeltaRuntimeImport:
    def test_api_and_configuration_import(self):
        _run(
            "from unitycatalog.delta import DeltaTablesApi, ApiClient, Configuration\n"
            "Configuration(host='http://localhost:8080')\n"
        )

    def test_serde_patch_auto_activates_without_manual_import(self):
        # Importing only the generated model (not the internal serde module)
        # must still pick up the from_dict/to_dict patches, since
        # models/__init__.py auto-imports the serde module as a side effect.
        _run(
            "from unitycatalog.delta.models.delta_struct_field import DeltaStructField\n"
            "import unitycatalog.delta.internal.serde.delta_data_type_module as m\n"
            "assert DeltaStructField.from_dict.__func__ is m._patched_sf_from_dict.__func__\n"
        )

    def test_rest_and_exceptions_import(self):
        _run(
            "from unitycatalog.delta.rest import RESTClientObject\n"
            "from unitycatalog.delta.exceptions import ApiException\n"
        )
