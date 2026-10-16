"""
Regression tests for generated ``from_dict``/``to_dict`` on the
``DeltaTableRequirement``/``DeltaTableUpdate`` discriminated subtype models
(``api/delta.yaml``'s ``allOf`` + ``discriminator`` hierarchies).

OpenAPI Generator 7.9.0's Python codegen computes ``allVars`` (used to render
``__properties``, ``to_dict()``, and ``from_dict()``) as just the *parent's*
vars for these subtypes, dropping every field the subtype itself declares.
That silently produced models whose generated ``from_dict`` raised a pydantic
``ValidationError`` for the subtype's own required fields (e.g. ``uuid`` on
``DeltaAssertTableUUID``), and whose ``__properties``/``to_dict`` omitted
those fields too. The fix is a narrowly scoped Python-only generator template
override (see ``clients/python/build/templates/README.md``); this file
verifies every affected subtype's own fields decode and round-trip, so the
template override can't silently regress.

These tests do NOT require a running server. They require generated models
(run `sbt pythonClient/generate` first).
"""

import pytest

from unitycatalog.delta.models.delta_table_requirement import DeltaTableRequirement
from unitycatalog.delta.models.delta_table_update import DeltaTableUpdate

# (discriminator wire dict, expected concrete class name, own-field assertions)
REQUIREMENT_CASES = [
    pytest.param(
        {"type": "assert-table-uuid", "uuid": "11111111-1111-1111-1111-111111111111"},
        "DeltaAssertTableUUID",
        {"uuid": "11111111-1111-1111-1111-111111111111"},
        id="assert-table-uuid",
    ),
    pytest.param(
        {"type": "assert-etag", "etag": 'W/"1"'},
        "DeltaAssertEtag",
        {"etag": 'W/"1"'},
        id="assert-etag",
    ),
]

UPDATE_CASES = [
    pytest.param(
        {"action": "set-properties", "updates": {"k": "v"}},
        "DeltaSetPropertiesUpdate",
        {"updates": {"k": "v"}},
        id="set-properties",
    ),
    pytest.param(
        {"action": "remove-properties", "removals": ["a", "b"]},
        "DeltaRemovePropertiesUpdate",
        {"removals": ["a", "b"]},
        id="remove-properties",
    ),
    pytest.param(
        {
            "action": "set-columns",
            "columns": {"type": "struct", "fields": [
                {"name": "id", "type": "long", "nullable": False, "metadata": {}},
            ]},
        },
        "DeltaSetSchemaUpdate",
        {},  # checked separately below (nested object field)
        id="set-columns",
    ),
    pytest.param(
        {"action": "set-table-comment", "comment": "hello"},
        "DeltaSetTableCommentUpdate",
        {"comment": "hello"},
        id="set-table-comment",
    ),
    pytest.param(
        {
            "action": "add-commit",
            "commit": {
                "version": 1,
                "timestamp": 123,
                "file-name": "00000000000000000001.json",
                "file-size": 10,
                "file-modification-timestamp": 123,
            },
        },
        "DeltaAddCommitUpdate",
        {},  # checked separately below (nested object field)
        id="add-commit",
    ),
    pytest.param(
        {"action": "set-latest-backfilled-version", "latest-published-version": 7},
        "DeltaSetLatestBackfilledVersionUpdate",
        {"latest_published_version": 7},
        id="set-latest-backfilled-version",
    ),
    pytest.param(
        {"action": "set-protocol", "protocol": {"min-reader-version": 1, "min-writer-version": 2}},
        "DeltaSetProtocolUpdate",
        {},  # checked separately below (nested object field)
        id="set-protocol",
    ),
    pytest.param(
        {
            "action": "set-domain-metadata",
            "updates": {"delta.clustering": {"clusteringColumns": [["a"]]}},
        },
        "DeltaSetDomainMetadataUpdate",
        {},  # checked separately below (nested object field)
        id="set-domain-metadata",
    ),
    pytest.param(
        {"action": "remove-domain-metadata", "domains": ["delta.clustering"]},
        "DeltaRemoveDomainMetadataUpdate",
        {"domains": ["delta.clustering"]},
        id="remove-domain-metadata",
    ),
    pytest.param(
        {"action": "set-partition-columns", "partition-columns": ["year", "month"]},
        "DeltaSetPartitionColumnsUpdate",
        {"partition_columns": ["year", "month"]},
        id="set-partition-columns",
    ),
    pytest.param(
        {
            "action": "update-metadata-snapshot-version",
            "last-commit-version": 5,
            "last-commit-timestamp-ms": 999,
        },
        "DeltaUpdateSnapshotVersionUpdate",
        {"last_commit_version": 5, "last_commit_timestamp_ms": 999},
        id="update-metadata-snapshot-version",
    ),
]


class TestDeltaTableRequirementSubtypes:
    @pytest.mark.parametrize("wire, expected_class, own_fields", REQUIREMENT_CASES)
    def test_decodes_own_fields(self, wire, expected_class, own_fields):
        obj = DeltaTableRequirement.from_dict(wire)
        assert type(obj).__name__ == expected_class
        for field, value in own_fields.items():
            assert getattr(obj, field) == value
        assert obj.to_dict() == wire


class TestDeltaTableUpdateSubtypes:
    @pytest.mark.parametrize("wire, expected_class, own_fields", UPDATE_CASES)
    def test_decodes_own_fields(self, wire, expected_class, own_fields):
        obj = DeltaTableUpdate.from_dict(wire)
        assert type(obj).__name__ == expected_class
        for field, value in own_fields.items():
            assert getattr(obj, field) == value
        # Every subtype field (not just scalars) must round-trip through to_dict(),
        # including nested-object own fields (columns/commit/protocol/updates above).
        assert obj.to_dict() == wire

    def test_set_schema_update_nested_columns(self):
        obj = DeltaTableUpdate.from_dict(UPDATE_CASES[2].values[0])
        assert obj.columns.fields[0].name == "id"

    def test_add_commit_update_nested_commit(self):
        obj = DeltaTableUpdate.from_dict(UPDATE_CASES[4].values[0])
        assert obj.commit.version == 1
        assert obj.commit.file_name == "00000000000000000001.json"

    def test_set_protocol_update_nested_protocol(self):
        obj = DeltaTableUpdate.from_dict(UPDATE_CASES[6].values[0])
        assert obj.protocol.min_reader_version == 1
        assert obj.protocol.min_writer_version == 2

    def test_set_domain_metadata_update_nested_updates(self):
        obj = DeltaTableUpdate.from_dict(UPDATE_CASES[7].values[0])
        assert obj.updates.delta_clustering.clustering_columns == [["a"]]
