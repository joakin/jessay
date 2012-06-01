
jessay
======

This is a static web generator.

By default this is going to generate a blog like index and a wiki like index.

The executable is generate.py, no dependencies except python 2.7 and perl
installed.

The web is published in the folder web/

Adapt your template in the template/ folder. It uses python default template
variables, like `$variable`, and there are only 3 vars, the relative path to
the index, the title for the page and where the content will be. Simple stuff.

To generate, go to the root of your folder and do `generate.py` if you have
made the script executable and is in your path. Else, just put the jessay
folder inside your page root, and do ./jessay/generate.py

TODO
----
* Regen only modified files
* Better validation and error messages
* Code style and better practices (python related)

Disclaimer
----------
This software is provided as is under a copyleft license. Feel free to improve
it and send pull requests. Feel free to use it, ignore it, modify it or
whatever you want to do.

The quality is not really good and it is the first project I've done in python,
so I don't really know conventions about code structure and readability.
Anyway, it does the trick for what it was created.


