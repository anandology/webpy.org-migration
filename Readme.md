# scripts for migrating webpy.org from infogami to github pages.

These scripts create a dump from webpy.org database and process that to generate a git repository.

## Required files:

* `data/spammers.txt` 

    File with email addresses of spammers. Edits by these users will be ignored when adding to git.

* `data/spamedits.txt`

    File with list of ids of the spam edits. These edits will be ignored when adding to git.

These files are be created by manually by looking at the edits and identifying spammers and spam edits.

## Building

* Generate the dump

        $ python process_db.py > data/dump.txt

* Process the dump

	    $ python process_dump.py < data/dump.txt
	
	Git repository will be created in `build` directory.
		
		$ cd build
		$ git log
		....
