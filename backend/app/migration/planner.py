from __future__ import annotations

from ..models import Finding, MigrationTask


class MigrationPlanner:
    def generate(self, inventory: list[Finding]) -> list[MigrationTask]:
        tasks: list[MigrationTask] = []
        for item in inventory:
            if item.recommended_replacement in {"Retain", "Retain / review usage"} or item.risk == "LOWER":
                continue
            dependencies = ["Protocol compatibility review", "Credential and key lifecycle plan"]
            if item.role == "Role Review Required":
                dependencies.insert(0, "Confirm cryptographic role")
            tasks.append(MigrationTask(
                inventory_id=item.id or 0, asset=item.asset, current_algorithm=item.algorithm,
                cryptographic_role=item.role, target_algorithm=item.recommended_replacement,
                reason=item.recommendation_reason, priority=item.priority, dependencies=dependencies,
                status="Planned",
            ))
        return tasks

