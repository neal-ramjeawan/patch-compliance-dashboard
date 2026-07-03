"""
DynamoDB-backed PatchRepository.

Single-table design:
  PK=INSTANCE#<id>, SK=LATEST          -> current state, overwritten each scan
  PK=INSTANCE#<id>, SK=SCAN#<ts>       -> historical record, for future trend views
  Per-patch detail is stored as a nested list attribute on the LATEST item
  rather than a second table, since fleet sizes here are small (~dozens to
  low hundreds of items well under DynamoDB's 400KB item limit).
"""

import boto3
from boto3.dynamodb.conditions import Key

from patch_domain.models import InstancePatchState, InstancePatch


class DynamoDBRepository:
    def __init__(self, table_name: str, dynamodb_resource=None):
        dynamodb = dynamodb_resource or boto3.resource("dynamodb")
        self._table = dynamodb.Table(table_name)

    def save_scan(
        self,
        states: list[InstancePatchState],
        patches_by_instance: dict[str, list[InstancePatch]],
    ) -> None:
        with self._table.batch_writer() as batch:
            for state in states:
                patches = patches_by_instance.get(state.instance_id, [])
                item = {
                    "PK": f"INSTANCE#{state.instance_id}",
                    "SK": "LATEST",
                    **state.to_dict(),
                    "patches": [p.to_dict() for p in patches],
                }
                batch.put_item(Item=item)

                # Historical record, kept separate so LATEST stays cheap to read
                history_item = dict(item)
                history_item["SK"] = f"SCAN#{state.scan_time}"
                batch.put_item(Item=history_item)

    def get_latest_states(self) -> list[InstancePatchState]:
        response = self._table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("SK").eq("LATEST"),
        )
        return [self._item_to_state(item) for item in response.get("Items", [])]

    def get_patches_for_instance(self, instance_id: str) -> list[InstancePatch]:
        response = self._table.get_item(
            Key={"PK": f"INSTANCE#{instance_id}", "SK": "LATEST"}
        )
        item = response.get("Item")
        if not item:
            return []
        return [InstancePatch(**p) for p in item.get("patches", [])]

    @staticmethod
    def _item_to_state(item: dict) -> InstancePatchState:
        fields = {k: v for k, v in item.items() if k in InstancePatchState.__dataclass_fields__}
        return InstancePatchState(**fields)
