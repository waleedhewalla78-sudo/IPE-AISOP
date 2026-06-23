# Unleash Feature Flag Server (self-hosted, free)
# Add to docker-compose.yml for local development
# When production Unleash is available, point JWT_USE_JWKS to Unleash API

# Add to infrastructure/docker/docker-compose.yml:
#
# unleash-server:
#   image: unleashorg/unleash-server:latest
#   container_name: ipe-unleash
#   ports:
#     - "4242:4242"
#   environment:
#     DATABASE_URL: "postgres://ipe:ipe_dev_pass@db:5432/ipe_dev"
#     DATABASE_SSL: "false"
#     INIT_ADMIN_API_TOKENS: '["*:*:development.unleash-insecure-api-token"]'
#   depends_on:
#     db:
#       condition: service_healthy
#   healthcheck:
#     test: ["CMD", "wget", "--spider", "-q", "http://localhost:4242/health"]
#     interval: 10s
#     timeout: 5s
#     retries: 5
#
# unleash-proxy:
#   image: unleashorg/unleash-proxy:latest
#   container_name: ipe-unleash-proxy
#   ports:
#     - "3063:3063"
#   environment:
#     UNLEASH_URL: "http://ipe-unleash:4242/api"
#     UNLEASH_APP_NAME: "ipe"
#     UNLEASH_AUTHORIZATION_TOKEN: "development.unleash-insecure-api-token"
#     UNLEASH_ENVIRONMENTS: "production,development"
#   depends_on:
#     - unleash-server
