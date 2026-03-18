from app.models.base import Base


def import_core_models() -> None:
    import app.models.tenant  # noqa: F401
    import app.models.user  # noqa: F401
    import app.models.access_control  # noqa: F401


def import_domain_models() -> None:
    import app.modules.hospitable.models.property_ops  # noqa: F401


def import_models() -> None:
    import_core_models()
    import_domain_models()