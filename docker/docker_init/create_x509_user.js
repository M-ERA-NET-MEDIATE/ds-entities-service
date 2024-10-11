db.getSiblingDB("$external").runCommand(
    {
      createUser: "CN=ds-entities-service,OU=Team4.0 Client,O=SINTEF,L=Trondheim,ST=Trondelag,C=NO",
      roles: [
           { role: "readWrite", db: "entities_service" }
      ],
    }
)

// Create the guest user on the admin database
db.getSiblingDB("admin").createUser(
    {
        user: "guest",
        pwd: "guest",
        roles: [
            { role: "read", db: "entities_service" }
        ]
    }
)
