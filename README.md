# SimByWire

## Publishing Docs

The documentation includes sections that document the public SimByWire interface,
as well as public-facing parts of the AirSim core library.  As such, they can
only be successfully generated on a machine that both libraries installed 
(i.e. not within the GitHub actions of the public SimByWire repository).

To generate the docs for internal review, `cd` into the SimByWire directory and
run `mkdocs serve`.

To publish to a website, run `mkdocs build --site-dir ../airsim-docs/public`,
which should be set up to point to a git-based hosting option, and then push the 
`airsim-docs` repo to a hosting service.
