AGM
===
.. image:: https://readthedocs.org/projects/agm/badge/?version=latest
   :target: https://agm.readthedocs.io/?badge=latest
   :alt: Documentation Status

.. image:: https://badge.fury.io/py/agm.svg
    :target: https://badge.fury.io/py/agm

.. image:: https://travis-ci.org/Cloudbakers/agm.svg?branch=master
    :target: https://travis-ci.org/Cloudbakers/agm

.. image:: https://img.shields.io/pypi/pyversions/agm.svg

AGM is an unofficial command line interface for Google APIs, written in Python. For example, if I wanted to get a list of all the items in my drive account, I would use the command:

.. code-block:: bash

   agm drive files list --user myemail@gmail.com --fields "*"

AGM will parse this command and efficiently execute these requests. AGM works with all `Google APIs <https://developers.google.com/apis-explorer/#p/>`_ and provides additional features which makes quickly processing data from Google's APIs simple and easy. It's great for debugging, G Suite administration, or simple task automation.

This tool is currenly in *Alpha*, so bugs are possible. Please report any issues to the `issues <https://github.com/Cloudbakers/agm/issues>`_ tab on GitHub. If you'd like to contribute, please let me know or submit a pull request!


Documentation
-------------

More detailed documentation can be found on `readthedocs <https://agm.readthedocs.io/?>`_!
