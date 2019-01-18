Using AGM
=========

Basic Usage
------------

.. literalinclude:: argparse.txt
   :language: text


AGM maps commands to the associated `Google API <https://developers.google.com/identity/protocols/googlescopes>`_. Not all APIs have been tested, so please report any issues to the `GitHub Issues <https://github.com/Cloudbakers/agm/issues>`_ page. Separate the API name (e.g. gmail) from the resources (e.g. user messages) from the method, like so:

.. code-block:: bash

   agm gmail users messages list --user myemail@gmail.com --maxResults 100 --userId me

This will return a json with a summary of the request and and the response from the server. If the request failed, the error message will be in the "error" field. You can provide a list for any parameter and AGM will iterate over that list. For example, if I wanted to get information about a list of files,

.. code-block:: bash

   agm drive files get --user myemail@gmail.com --fileId abc def ghi

And AGM will iterate over that list in order to get information about each file. If you provide multiple values for multiple parameters, AGM will iterate over each list together. AGM uses batch requests and multithreading for high performance, so AGM is especially suitable for very large, long-running tasks that involve many API requests.

For documentation on a command, run the command with the :code:`-d` or :code:`--docs` flag. This flag can be ommitted if you want information about a service or resource. Just typing :code:`agm` will list all of the available APIs.

If :code:`--outfile` is ommitted, output will be printed to the console.

Logs are in ~/.agm/logs. Check them for debugging or if you need a record of recent actions performed by AGM.

Piping input
------------

You can pipe input into AGM. For our previous command, if we wanted to get information about a large number of files, we could save these files to a text document, files.txt, and then pipe that file into AGM:


.. code-block:: bash

   cat files.txt | agm drive files get --user myemail@gmail.com --fileId

AGM will also accept a json string as piped input of the format:

.. code-block:: json

    {
      "parameter": "value"
    }
   


