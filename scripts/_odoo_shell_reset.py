admin = env["res.users"].search([("login", "=", "admin")], limit=1)
if not admin:
    admin = env["res.users"].search([("share", "=", False)], order="id asc", limit=1)
admin.write({"password": "admin"})
env.cr.commit()
print("OK login=%s id=%s" % (admin.login, admin.id))
