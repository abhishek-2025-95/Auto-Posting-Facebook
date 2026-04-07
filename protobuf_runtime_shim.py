"""
google.protobuf 5+ generated code (e.g. duration_pb2) expects:

  google.protobuf.runtime_version.Domain.PUBLIC
  google.protobuf.runtime_version.ValidateProtobufRuntimeVersion(...)

Older stubs in this repo only added ValidateProtobufRuntimeVersion, which breaks
`from google.cloud import aiplatform` on system Python with protobuf 5.x.

Import this module early (before google.cloud / generated pb2) — it is idempotent.
"""
from __future__ import annotations

import enum
import types


def apply_protobuf_runtime_version_shim() -> None:
    try:
        import google.protobuf as _gp
    except Exception:
        return

    _rv = getattr(_gp, "runtime_version", None)

    class Domain(enum.IntEnum):
        """Matches google.protobuf.runtime_version.Domain (values used by generated code)."""

        PUBLIC = 0
        PRIVATE = 1

    def ValidateProtobufRuntimeVersion(*_args, **_kwargs):
        return None

    if _rv is not None and hasattr(_rv, "Domain") and hasattr(_rv, "ValidateProtobufRuntimeVersion"):
        return

    if _rv is not None and hasattr(_rv, "ValidateProtobufRuntimeVersion") and not hasattr(_rv, "Domain"):
        _rv.Domain = Domain
        return

    _mod = types.ModuleType("runtime_version")
    _mod.Domain = Domain
    _mod.ValidateProtobufRuntimeVersion = ValidateProtobufRuntimeVersion
    _gp.runtime_version = _mod


apply_protobuf_runtime_version_shim()
