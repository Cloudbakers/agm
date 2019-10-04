# Installation and Setup

## Installation

AGM requires Python>=3.5. I haven't tested installation on Windows, but I plan on building it soon.

To install AGM via pip, run this command:
```
pip install --user agm
```
If you don't have pip installed, follow [this guide](https://docs.python-guide.org/starting/installation/). Depending on your Python environment, you may need to run `pip3` instead of `pip`. If you haven't set up a Python environment on your machine and are using a Linux-based system, you may need to add the line `export PATH=$PATH":$HOME/.local/bin"` to your `~/.bashrc` file.

## Setup

AGM can be authenticated in two ways, via service account or through individual accounts via OAuth2. Using a service account is useful if you're a developer or G Suite administrator, whereas individual authentication is useful if you're acting on behalf of a single account, a consumer Google account or a list of consumer Google accounts.

### Service account authentication

First, follow Google's guide for [Using OAuth 2.0 for Server to Server Applications](https://developers.google.com/identity/protocols/OAuth2ServiceAccount#creatinganaccount). Put this JSON keyfile into `~/.agm/` (preferred) or pass it into AGM with the `--keyfile` flag. Beware this key is tremendously powerful. Keep it secret and safe and don't share it with anyone! Be mindful of the scopes you are using and refurnish a new key from time to time.

Make sure any APIs you wanna use are enabled in the project associated with your service account!


### Individual OAuth2 authentication

Navigate to the [Google API credentials page](https://console.developers.google.com/apis/credentials).

If you haven't set up this project yet, you will need to configure your OAuth2 consent screen. Fill out the Application Name field (I recommend "AGM") and leave all the other fields as defaults.

Select "Create Crenedentials" and "OAuth Client ID". Select "Other" for application type and give your client a name (I recommend AGM). On the credentials page, download the client secret and save it into `~/.agm/client_secret.json`. This client secret will serve as the indentifier of your AGM installation, you can freely use the same client secret to authenticate many individual Google accounts.

In order to run the oauth authentication, use the following command:
```
agm --run-oauth --user [emaill_to_authenticate] --scopes [scopes to grant]*
```

You may receive a warning at this point. Click "advanced" and proceed anyway.

\*See the list of [API scopes](https://developers.google.com/identity/protocols/googlescopes) and decide on the scopes that you need for your purpose. You can always change these by running this command again with different scopes.

Authenticated credentials will be stored in `~/.agm/oauth_credentials`. These keys are sensitive, so keep them safe and regularly delete any old credentials you don't need anymore.

You will now be able to make AGM requests on behalf of this user, by specifying them with the `--user` parameter.
