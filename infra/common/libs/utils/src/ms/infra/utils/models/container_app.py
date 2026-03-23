from ms.infra.utils.models.docker_config_base import DockerConfigBase


class ContainerApp(DockerConfigBase):
    """
    Base configuration for Azure Container Apps.
    """

    replicas_min: int
    replicas_max: int
    cpu: float = 0.5
    memory_in_gb: float = 1.0
    ingress_target_port: int = 80
    ingress_transport_external: bool = True
    concurrent_requests_per_replica: int = 50
