import uuid
from typing import Any

import pulumi
import pulumi_docker_build as docker_build
from pulumi_azure_native import containerregistry
from pulumi_azure_native.resources import ResourceGroup
from pulumi_command import local as command

from ms.infra.core.settings import settings
from ms.infra.utils.models.docker_config_base import DockerConfigBase

# Azure AD token-based ACR auth uses this fixed username
_ACR_AAD_TOKEN_USERNAME = "00000000-0000-0000-0000-000000000000"


def create_and_login_acr(
    resource_group: ResourceGroup,
) -> tuple[containerregistry.Registry, command.Command]:
    acr = containerregistry.Registry(
        "acr",
        resource_group_name=resource_group.name,
        sku=containerregistry.SkuArgs(name="Standard"),
        admin_user_enabled=False,
    )

    # Fetch an AAD access token for the ACR. This uses whatever Azure identity is
    # currently active (user, service principal, or managed identity).
    # The token is passed explicitly to docker_build.Image via registries, since
    # pulumi_docker_build's embedded BuildKit does not read Docker's credential store.
    unique_id = str(uuid.uuid4())
    acr_login = command.Command(
        "acr-login",
        create=pulumi.Output.all(
            "az",
            "acr",
            "login",
            "--name",
            acr.name,
            "--expose-token",
            "--output tsv",
            "--query accessToken",
        ).apply(lambda args: " ".join(args)),
        # Suppress logging since the access token is included in the command output
        logging=command.Logging.NONE,
        triggers=[unique_id],
        opts=pulumi.ResourceOptions(
            depends_on=[acr],
            # Mark stdout as a secret since ACR access token is logged via stdout
            additional_secret_outputs=["stdout"],
        ),
    )

    return acr, acr_login


def build_docker_image(
    acr: containerregistry.Registry,
    acr_login: command.Command,
    app: DockerConfigBase,
    additional_build_args: dict[str, str | pulumi.Output[Any]] | None = None,
) -> docker_build.Image:
    image_tag = settings.build_id

    app_name = app.app_name
    app_path = app.app_path
    dockerfile_abs = (settings.repo_root / app.dockerfile_path).resolve()
    context_root = settings.repo_root / app.docker_build_context

    if not dockerfile_abs.is_file():
        raise FileNotFoundError(f"Required Dockerfile not found at {dockerfile_abs} for app '{app_name}'.")

    # Build & push container
    image_name = pulumi.Output.concat(acr.login_server, "/", app_name, ":", image_tag)

    image = docker_build.Image(
        f"{app_name}-image",
        tags=[image_name],
        context=docker_build.BuildContextArgs(location=str(context_root)),
        dockerfile=docker_build.DockerfileArgs(location=str(dockerfile_abs)),
        build_args={
            "APP_PATH": app_path,
            **({"LIBS_PATH": app.libs_path} if app.libs_path else {}),
            **(app.build_args if app.build_args else {}),
            **(additional_build_args if additional_build_args else {}),
        },
        platforms=[docker_build.Platform.LINUX_AMD64],
        push=True,
        registries=[
            docker_build.RegistryArgs(
                address=acr.login_server,
                username=_ACR_AAD_TOKEN_USERNAME,
                password=acr_login.stdout.apply(lambda s: s.strip()),
            ),
        ],
        opts=pulumi.ResourceOptions(depends_on=[acr_login]),
    )

    return image
