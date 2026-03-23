from dataclasses import dataclass

import pulumi
from pulumi_azure_native import authorization

from ms.infra.utils.roles import BuiltInRole


@dataclass(frozen=True)  # 3rd party type pulumi.Input not compatible with pydantic
class RoleAssignmentInfo:
    name: str
    role: BuiltInRole
    scope: pulumi.Input[str]

    def create_service_principal_role_assignment(
        self,
        principal_id: pulumi.Input[str],
        prefix: str | None = None,
    ) -> authorization.RoleAssignment:
        return authorization.RoleAssignment(
            f"{prefix}-{self.name}" if prefix else self.name,
            role_definition_id=self.role.to_definition_id(),
            principal_id=principal_id,
            principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
            scope=self.scope,
        )
