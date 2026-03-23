from typing import Literal

from ms.infra.core.models.base import FrozenBaseModel


class DockerConfigBase(FrozenBaseModel):
    """
    Base configuration for Docker-based deployments.
    """

    app_name: str
    dockerfile_path: str
    docker_build_context: Literal[".", "py", "ts"]
    app_path: str
    libs_path: str | None = None
    env: dict[str, str] | None = None
    build_args: dict[str, str] | None = None  # Custom build arguments for Docker
