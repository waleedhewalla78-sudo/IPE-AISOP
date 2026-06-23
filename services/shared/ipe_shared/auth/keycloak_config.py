"""Keycloak mock configuration for IPE demo.

Provides a working Keycloak setup with:
- IPE realm with all required OIDC/SAML/SCIM settings
- Test users for all roles (admin, planner, operator, viewer)
- Pre-configured clients for frontend and backend
- SAML 2.0 identity provider placeholders
- SCIM 2.0 user/group provisioning endpoints
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeycloakRealm:
    name: str = "ipe"
    display_name: str = "IPE Manufacturing Platform"
    enabled: bool = True
    ssl_required: str = "external"
    registration_allowed: bool = False
    login_with_email_allowed: bool = True
    duplicate_emails_allowed: bool = False
    reset_password_allowed: bool = True
    edit_username_allowed: bool = False
    brute_force_protected: bool = True
    max_failure_wait_seconds: int = 900
    minimum_quick_login_wait_seconds: int = 60
    wait_increment_seconds: int = 60
    quick_login_check_milli_seconds: int = 1000
    max_delta_time_seconds: int = 43200
    password_policy: str = "length(12) and upperCase(1) and lowerCase(1) and digits(1) and specialChars(1)"
    token_lifespan: int = 300
    sso_session_idle_timeout: int = 1800
    sso_session_max_lifespan: int = 36000


@dataclass
class OIDCClient:
    client_id: str
    client_secret: str
    name: str
    enabled: bool = True
    protocol: str = "openid-connect"
    public_client: bool = False
    standard_flow_enabled: bool = True
    implicit_flow_enabled: bool = False
    direct_access_grants_enabled: bool = True
    service_accounts_enabled: bool = False
    redirect_uris: list[str] = field(default_factory=list)
    web_origins: list[str] = field(default_factory=list)
    default_client_scopes: list[str] = field(default_factory=list)
    protocol_mappers: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SAMLClient:
    client_id: str
    name: str
    enabled: bool = True
    protocol: str = "saml"
    assertion_consumer_service_url: str = ""
    single_logout_service_url: str = ""
    certificate: str = ""
    sign_assertions: bool = True
    sign_documents: bool = True
    force_name_id_format: bool = True
    name_id_format: str = "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"


@dataclass
class TestUser:
    username: str
    email: str
    password: str
    first_name: str
    last_name: str
    roles: list[str] = field(default_factory=list)
    tenant_id: str = ""


@dataclass
class SCIMConfig:
    enabled: bool = True
    scim_base_url: str = "/realms/ipe/protocol/scim"
    supported_schemas: list[str] = field(default_factory=lambda: [
        "urn:ietf:params:scim:schemas:core:2.0:User",
        "urn:ietf:params:scim:schemas:core:2.0:Group",
        "urn:ietf:params:scim:api:messages:2.0:ListResponse",
        "urn:ietf:params:scim:api:messages:2.0:PatchOp",
    ])


# IPE Realm Configuration
IPE_REALM = KeycloakRealm()

# OIDC Clients
OIDC_CLIENTS = [
    OIDCClient(
        client_id="ipe-frontend",
        client_secret=os.environ.get("KEYCLOAK_FRONTEND_CLIENT_SECRET", "CHANGE_ME_IN_PRODUCTION"),
        name="IPE Frontend (React)",
        redirect_uris=[
            "http://localhost:3000/*",
            "https://app.ipe.ai/*",
        ],
        web_origins=[
            "http://localhost:3000",
            "https://app.ipe.ai",
        ],
        default_client_scopes=[
            "openid", "profile", "email", "ipe-roles", "ipe-tenants",
        ],
        protocol_mappers=[
            {
                "name": "realm-roles",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-realm-role-mapper",
                "config": {"multivalued": "true", "id.token.claim": "true", "access.token.claim": "true"},
            },
            {
                "name": "tenant-id",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {"user.attribute": "tenant_id", "id.token.claim": "true", "access.token.claim": "true", "claim.name": "tenant_id"},
            },
            {
                "name": "user-id",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-usermodel-attribute-mapper",
                "config": {"user.attribute": "uuid", "id.token.claim": "true", "access.token.claim": "true", "claim.name": "sub"},
            },
        ],
    ),
    OIDCClient(
        client_id="ipe-backend",
        client_secret=os.environ.get("KEYCLOAK_BACKEND_CLIENT_SECRET", "CHANGE_ME_IN_PRODUCTION"),
        name="IPE Backend Services",
        service_accounts_enabled=True,
        direct_access_grants_enabled=True,
        standard_flow_enabled=False,
        default_client_scopes=[
            "openid", "profile", "email", "ipe-roles", "ipe-tenants",
        ],
    ),
]

# SAML 2.0 Client (for Azure AD / Okta federation)
SAML_CLIENT = SAMLClient(
    client_id="ipe-saml",
    name="IPE SAML Federation",
    assertion_consumer_service_url="https://app.ipe.ai/auth/realms/ipe/broker/saml/endpoint",
    single_logout_service_url="https://app.ipe.ai/auth/realms/ipe/broker/saml/endpoint/logout",
)

# Test Users (for demo)
TEST_USERS = [
    TestUser(
        username="admin",
        email="admin@ipe.ai",
        password=os.environ.get("KEYCLOAK_ADMIN_PASSWORD", "CHANGE_ME_IN_PRODUCTION"),
        first_name="Admin",
        last_name="User",
        roles=["admin", "planner", "manager", "executive"],
        tenant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    ),
    TestUser(
        username="planner",
        email="planner@ipe.ai",
        password=os.environ.get("KEYCLOAK_PLANNER_PASSWORD", "CHANGE_ME_IN_PRODUCTION"),
        first_name="Production",
        last_name="Planner",
        roles=["planner"],
        tenant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    ),
    TestUser(
        username="operator",
        email="operator@ipe.ai",
        password=os.environ.get("KEYCLOAK_OPERATOR_PASSWORD", "CHANGE_ME_IN_PRODUCTION"),
        first_name="Shop Floor",
        last_name="Operator",
        roles=["operator"],
        tenant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    ),
    TestUser(
        username="viewer",
        email="viewer@ipe.ai",
        password=os.environ.get("KEYCLOAK_VIEWER_PASSWORD", "CHANGE_ME_IN_PRODUCTION"),
        first_name="Read Only",
        last_name="User",
        roles=["viewer"],
        tenant_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
    ),
]

# SCIM Configuration
SCIM_CONFIG = SCIMConfig()


def generate_realm_json() -> dict[str, Any]:
    """Generate complete Keycloak realm JSON for import."""
    return {
        "realm": IPE_REALM.name,
        "displayName": IPE_REALM.display_name,
        "enabled": IPE_REALM.enabled,
        "sslRequired": IPE_REALM.ssl_required,
        "registrationAllowed": IPE_REALM.registration_allowed,
        "loginWithEmailAllowed": IPE_REALM.login_with_email_allowed,
        "duplicateEmailsAllowed": IPE_REALM.duplicate_emails_allowed,
        "resetPasswordAllowed": IPE_REALM.reset_password_allowed,
        "editUsernameAllowed": IPE_REALM.edit_username_allowed,
        "bruteForceProtected": IPE_REALM.brute_force_protected,
        "passwordPolicy": IPE_REALM.password_policy,
        "accessTokenLifespan": IPE_REALM.token_lifespan,
        "ssoSessionIdleTimeout": IPE_REALM.sso_session_idle_timeout,
        "ssoSessionMaxLifespan": IPE_REALM.sso_session_max_lifespan,
        "roles": {
            "realm": [
                {"name": "admin", "description": "Full system administrator"},
                {"name": "planner", "description": "Production planner with scheduling access"},
                {"name": "operator", "description": "Shop floor operator with limited access"},
                {"name": "viewer", "description": "Read-only access to dashboards"},
                {"name": "manager", "description": "Department manager with approval access"},
                {"name": "executive", "description": "Executive with financial and strategic access"},
            ],
        },
        "users": [
            {
                "username": u.username,
                "email": u.email,
                "firstName": u.first_name,
                "lastName": u.last_name,
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"type": "password", "value": u.password, "temporary": False}],
                "realmRoles": u.roles,
                "attributes": {"tenant_id": [u.tenant_id]},
            }
            for u in TEST_USERS
        ],
        "clients": [
            {
                "clientId": c.client_id,
                "name": c.name,
                "enabled": c.enabled,
                "protocol": c.protocol,
                "publicClient": c.public_client,
                "standardFlowEnabled": c.standard_flow_enabled,
                "implicitFlowEnabled": c.implicit_flow_enabled,
                "directAccessGrantsEnabled": c.direct_access_grants_enabled,
                "serviceAccountsEnabled": c.service_accounts_enabled,
                "redirectUris": c.redirect_uris,
                "webOrigins": c.web_origins,
                "secret": c.client_secret,
                "defaultClientScopes": c.default_client_scopes,
                "protocolMappers": c.protocol_mappers,
            }
            for c in OIDC_CLIENTS
        ],
        "clientScopes": [
            {
                "name": "ipe-roles",
                "description": "IPE user roles",
                "protocol": "openid-connect",
                "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"},
                "protocolMappers": [
                    {
                        "name": "ipe-roles-mapper",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-realm-role-list-mapper",
                        "config": {"multivalued": "true", "id.token.claim": "true", "access.token.claim": "true"},
                    }
                ],
            },
            {
                "name": "ipe-tenants",
                "description": "IPE tenant isolation",
                "protocol": "openid-connect",
                "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"},
                "protocolMappers": [
                    {
                        "name": "tenant-id-mapper",
                        "protocol": "openid-connect",
                        "protocolMapper": "oidc-usermodel-attribute-mapper",
                        "config": {"user.attribute": "tenant_id", "id.token.claim": "true", "access.token.claim": "true", "claim.name": "tenant_id"},
                    }
                ],
            },
        ],
    }


def get_demo_jwt_claims(username: str = "admin") -> dict[str, Any]:
    """Generate demo JWT claims for testing without Keycloak server."""
    user = next((u for u in TEST_USERS if u.username == username), TEST_USERS[0])
    return {
        "sub": f"demo-user-{user.username}",
        "email": user.email,
        "preferred_username": user.username,
        "given_name": user.first_name,
        "family_name": user.last_name,
        "realm_access": {"roles": user.roles},
        "tenant_id": user.tenant_id,
        "iat": 1700000000,
        "exp": 1800000000,
        "iss": "http://localhost:8180/realms/ipe",
        "aud": "ipe-backend",
    }
