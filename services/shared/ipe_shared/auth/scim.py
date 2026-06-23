"""SCIM 2.0 endpoints for user provisioning.

Implements RFC 7644 (SCIM Protocol) endpoints for user and group management.
Maps SCIM users to IPE's internal user model with tenant-aware role assignment.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ipe_shared.auth.jwt import TokenPayload
from ipe_shared.auth.rbac import require_roles
from ipe_shared.middleware.tenant_context import tenant_ctx
from ipe_shared.schemas.common import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scim/v2", tags=["scim"])

_user_store: dict[str, dict] = {}
_group_store: dict[str, dict] = {}


@router.get("/Users")
async def list_users(
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1, le=500),
    filter: str | None = Query(None),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    tenant_id = tenant_ctx.get()
    users = [u for u in _user_store.values() if u.get("tenant_id") == str(tenant_id) or tenant_id is None]
    if filter:
        parts = filter.split("eq")
        if len(parts) == 2:
            field = parts[0].strip().replace('"', "")
            value = parts[1].strip().replace('"', "")
            users = [u for u in users if str(u.get(field, "")).lower() == value.lower()]
    total = len(users)
    page = users[(startIndex - 1):(startIndex - 1 + count)]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": total,
        "startIndex": startIndex,
        "itemsPerPage": min(count, len(page)),
        "Resources": page,
    }


@router.post("/Users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: dict,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    tenant_id = tenant_ctx.get() or str(uuid4())
    user_id = str(uuid4())
    scim_user = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": user_id,
        "userName": user.get("userName", ""),
        "name": user.get("name", {}),
        "emails": user.get("emails", []),
        "active": user.get("active", True),
        "tenant_id": tenant_id,
        "role": user.get("role", "operator"),
        "title": user.get("title", ""),
        "department": user.get("department", ""),
        "meta": {
            "resourceType": "User",
            "created": datetime.now(UTC).isoformat(),
            "lastModified": datetime.now(UTC).isoformat(),
            "location": f"/scim/v2/Users/{user_id}",
        },
    }
    _user_store[user_id] = scim_user
    logger.info("SCIM user created: %s (tenant=%s)", user_id, tenant_id)
    return scim_user


@router.get("/Users/{user_id}")
async def get_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_roles(["admin", "planner", "manager"])),
):
    user = _user_store.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


@router.put("/Users/{user_id}")
async def update_user(
    user_id: str,
    user: dict,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    existing = _user_store.get(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    existing.update({
        "userName": user.get("userName", existing.get("userName")),
        "name": user.get("name", existing.get("name", {})),
        "emails": user.get("emails", existing.get("emails", [])),
        "active": user.get("active", existing.get("active", True)),
        "role": user.get("role", existing.get("role", "operator")),
        "title": user.get("title", existing.get("title", "")),
        "department": user.get("department", existing.get("department", "")),
    })
    existing["meta"]["lastModified"] = datetime.now(UTC).isoformat()
    logger.info("SCIM user updated: %s", user_id)
    return existing


@router.patch("/Users/{user_id}")
async def patch_user(
    user_id: str,
    operations: dict,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    existing = _user_store.get(user_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    for op in operations.get("Operations", []):
        op_type = op.get("op", "").lower()
        path = op.get("path", "")
        value = op.get("value")
        if op_type == "replace" and path:
            existing[path] = value
        elif op_type == "replace" and isinstance(value, dict):
            existing.update(value)
    existing["meta"]["lastModified"] = datetime.now(UTC).isoformat()
    return existing


@router.delete("/Users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    if user_id not in _user_store:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    del _user_store[user_id]
    logger.info("SCIM user deleted: %s", user_id)


@router.get("/Groups")
async def list_groups(
    startIndex: int = Query(1, ge=1),
    count: int = Query(100, ge=1, le=500),
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    groups = list(_group_store.values())
    total = len(groups)
    page = groups[(startIndex - 1):(startIndex - 1 + count)]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": total,
        "startIndex": startIndex,
        "itemsPerPage": min(count, len(page)),
        "Resources": page,
    }


@router.post("/Groups", status_code=status.HTTP_201_CREATED)
async def create_group(
    group: dict,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    group_id = str(uuid4())
    scim_group = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
        "id": group_id,
        "displayName": group.get("displayName", ""),
        "members": group.get("members", []),
        "meta": {
            "resourceType": "Group",
            "created": datetime.now(UTC).isoformat(),
            "lastModified": datetime.now(UTC).isoformat(),
            "location": f"/scim/v2/Groups/{group_id}",
        },
    }
    _group_store[group_id] = scim_group
    return scim_group


@router.get("/Groups/{group_id}")
async def get_group(
    group_id: str,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    group = _group_store.get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    return group


@router.delete("/Groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    if group_id not in _group_store:
        raise HTTPException(status_code=404, detail=f"Group {group_id} not found")
    del _group_store[group_id]


@router.get("/Schemas")
async def list_schemas():
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "Resources": [
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:User",
                "name": "User",
                "description": "IPE User Account",
                "attributes": [
                    {"name": "userName", "type": "string", "multiValued": False, "required": True},
                    {"name": "name", "type": "complex", "multiValued": False, "required": False},
                    {"name": "emails", "type": "complex", "multiValued": True, "required": False},
                    {"name": "active", "type": "boolean", "multiValued": False, "required": False},
                    {"name": "tenant_id", "type": "string", "multiValued": False, "required": True},
                    {"name": "role", "type": "string", "multiValued": False, "required": False},
                ],
            },
            {
                "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
                "name": "Group",
                "description": "IPE User Group",
                "attributes": [
                    {"name": "displayName", "type": "string", "multiValued": False, "required": True},
                    {"name": "members", "type": "complex", "multiValued": True, "required": False},
                ],
            },
        ],
    }


@router.post("/Bulk")
async def bulk_operation(
    bulk_request: dict,
    current_user: TokenPayload = Depends(require_roles(["admin"])),
):
    results = []
    for operation in bulk_request.get("Operations", []):
        method = operation.get("method", "GET").upper()
        path = operation.get("path", "")
        data = operation.get("data", {})
        status_code = 200
        response_data = {}

        if method == "POST" and "/Users" in path:
            user_id = str(uuid4())
            new_user = {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": user_id,
                "userName": data.get("userName", ""),
                "active": data.get("active", True),
                "role": data.get("role", "operator"),
                "tenant_id": data.get("tenant_id", str(tenant_ctx.get() or uuid4())),
            }
            _user_store[user_id] = new_user
            status_code = 201
            response_data = new_user
        elif method == "DELETE" and "/Users/" in path:
            uid = path.split("/Users/")[-1]
            if uid in _user_store:
                del _user_store[uid]
                status_code = 204
            else:
                status_code = 404

        results.append({
            "method": method,
            "path": path,
            "status": status_code,
            "response": response_data,
        })

    return {"schemas": ["urn:ietf:params:scim:api:messages:2.0:BulkResponse"], "Operations": results}