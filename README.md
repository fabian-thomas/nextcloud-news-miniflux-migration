This repo contains code that should help in migrating a Nextcloud news instance with the full history to Miniflux.
Make sure to do backups of both your Nextcloud and Miniflux files prior to testing anything.
The migration only reads the Nextcloud database.
The tables for feeds, items and categories of the Miniflux database are completely cleared during migration.

# Dependencies

Init a nix shell from the `shell.nix` file so that you have all the dependencies.
You can also use a pyenv. Just make sure that all packages are there.
``` sh
nix-shell shell.nix
```

# Nextcloud Connection
Depending on your Nextcloud setup you might need to bind the mysqld socket to your host, e.g., when running in docker or in a NixOS container.
In a docker compose file you can bind the mysqld sockets by adding a volume:

``` yaml
volumes:
- /tmp/nextcloud-mysqld:/var/run/mysqld
```

Note: Make sure to create the directory `/tmp/nextcloud-mysqld` prior to starting the container.

# Miniflux Connection
Depending on your Miniflux setup you might run into problems where you cant access the database.
I found no nice way (i.e. without modifying configs) to access the database in a container.
Therefore I run the migration outside a container and then move the database files into a container.

The script connects to the Miniflux database by changing the user to `miniflux`.
This might too vary depending on your setup.
I use the NixOS Miniflux service.

# Migration
Run the migration. Note again that you should do a backup of your prior miniflux data since feeds, items and categories will be *completely* deleted.
``` sh
sudo python migrate.py <nextcloud-pw> <nextcloud-socket-dir>
```

Note: Running as root is needed to change the user to miniflux so that we can access the miniflux database.
This might vary depending on your setup. Note that the socket dir is the one that you mounted before into your container (i.e. `/tmp/nextcloud-mysqld`).
