# RMG Website - A Django-powered website for RMG

This repository contains the source code that powers the RMG website, which runs at http://rmg.mit.edu/.
The RMG website itself uses the [Django](http://www.djangoproject.com/) web framework.

## User Setup

If you only wish to *use* the RMG website, no setup is required!
Simply point your favorite web browser to http://rmg.mit.edu/ to get started.
Some parts of the web site require that Javascript be enabled.

## Developer Setup

Running RMG-website requires a working installation of [RMG-Py](http://github.com/ReactionMechanismGenerator/RMG-Py). 
Development of the website closely mirrors that of RMG-Py, and you will generally need to update the RMG-Py repository whenever you update this repository.

### 1. Setup Dependencies
Clone the `RMG-website` repo into your local folder.  

The following command will update your `rmg_env` environment and install the necessary packages for RMG-website
```
cd RMG-website
conda env update -f environment.yml
pip install git+https://github.com/bp-kelley/descriptastorus
```

### 2. Configure the Webserver
In order to get the webserver running, you must first create a `secretsettings.py` file.
This file is intended to hold settings that are specific to a particular installation.
An example file is provided in `rmgweb/secretsettings.py.example`.
Make a copy of that file named `secretsettings.py`.

Django uses a secret key for cryptographic signing, which is set in `secretsettings.py`.
A dummy key is provided in the example file, which will work for basic use.
For production environments, it is strongly recommended to generate a custom key.
Instructions to generate a key using Python are provided in the example file, or you can use an online tool.

You also need to add `'127.0.0.1'` to `ALLOWED_HOSTS` in `secretsettings.py` to run RMG-website locally.

### 3. Run the Website
If running the website for the first time, enter the commands
```
cd RMG-website
python manage.py migrate
python manage.py runserver
```

You may be prompted to create a superuser account, which you will need to access admin features on the website.

Now the website should appear on your localhost, you can visit it in any browser using the URL: http://127.0.0.1:8000/.
The website may take some time to load, as the RMG database must be loaded from the disk every time the webserver is restarted.

### 4. Usage Notes
When you rebuild any `Model` class within a models.py file, you have to modify the sql tables. This step is more complex now that Django has moved to a migration model.

For production, it is necessary to create a migration. However, RMG-website has not fully transitioned to using migrations, so detailed instructions are not available at this point.

For local development, it is possible to simply recreate the necessary database tables. For instance if you changed `rmgweb/rmg/models.py`, the module name is `rmg`.

1. Generate sql commands for dropping the tables:

    ```
    python manage.py sqlclear rmg
    ```

2. Copy the section starting with `BEGIN` and ending with `COMMIT`.
3. Start the database shell:

    ```
    python manage.py dbshell
    ```

4. Paste the copied commands, then use `CRTL+D` to exit.
5. Regenerate the tables and start the server:

    ```
    python manage.py migrate
    python manage.py runserver
    ```

## Credits
- [Professor William H. Green's research group](http://cheme.scripts.mit.edu/green-group/) at the 
[Massachusetts Institute of Technology](http://web.mit.edu/) 
- [Professor Richard H. West's research group](http://www.northeastern.edu/comocheng/) at 
[Northeastern University](http://www.northeastern.edu/)

## How to Give Feedback

Please post any issues you may have to the [issues page](https://github.com/ReactionMechanismGenerator/RMG-website/issues/) or email [rmg_dev@mit.edu](mailto:rmg_dev@mit.edu) if you have questions.
