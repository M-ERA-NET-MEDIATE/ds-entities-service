db.getSiblingDB("admin").createUser(
    {
        user: "dataspaces",
        pwd: "dataspaces",
        roles: [
            { role: "readWrite", db: "entities_service" }
        ]
    }
)
