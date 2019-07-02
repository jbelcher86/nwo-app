# nWo Wrestler Catalog

Relive the glory days of 90's WCW with this very simple flask app. Create your own nWo faction and assign wrestlers to it. This app uses Google's OAuth to
register and authenticate users. Once a user is authenticated, they have the ability to add, delete, or edit any faction or wrestler they create.

## Set Up

1. Clone the [fullstack-nanodegree-vm repository](https://github.com/udacity/fullstack-nanodegree-vm).
This repo contains the vagrant file necessary to run the app.

2. Look for the *catalog* folder and replace it with the contents of this respository.

## Usage

Launch the Vagrant VM from inside the *vagrant* folder with:

`vagrant up`

Then access the shell with:

`vagrant ssh`

Then move inside the catalog folder:

`cd /vagrant/catalog`

Create the db with:

`python database.py`

Populate the database with initial values using:

`python populate_db.py`

Then run the app:

`python application.py`

The application can then be found at:

`http://localhost:5000/`

Once you are done, close the app with:

`ctrl-c`