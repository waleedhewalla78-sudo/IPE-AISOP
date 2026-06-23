local kong = kong

local IpeTenantStripHandler = {
  VERSION = "1.0.0",
  PRIORITY = 1000,
}

local function b64url_decode(input)
  local padded = input .. string.rep("=", 4 - #input % 4)
  local std = padded:gsub("-", "+"):gsub("_", "/")
  return ngx.decode_base64(std)
end

local function decode_jwt_payload(auth_header)
  if not auth_header then
    return nil
  end

  local token = auth_header:match("[Bb]earer%s+(.+)")
  if not token then
    return nil
  end

  local segments = {}
  for segment in token:gmatch("[^.]+") do
    segments[#segments + 1] = segment
  end

  if #segments ~= 3 then
    return nil
  end

  local decoded = b64url_decode(segments[2])
  if not decoded then
    return nil
  end

  local cjson = require("cjson.safe")
  local ok, payload = pcall(cjson.decode, decoded)
  if ok and payload then
    return payload
  end

  return nil
end

function IpeTenantStripHandler:access(conf)
  kong.service.request.clear_header("X-Tenant-ID")

  local auth_header = kong.request.get_header("Authorization")
  local payload = decode_jwt_payload(auth_header)

  if payload and payload.tenant_id then
    kong.service.request.set_header("X-Tenant-ID", tostring(payload.tenant_id))
  else
    kong.log.warn("ipe-tenant-strip: no tenant_id claim in JWT payload or token missing")
  end
end

return IpeTenantStripHandler