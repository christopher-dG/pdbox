import dropbox
import os
import pdbox
import requests

from pdbox.utils import fail


def get_token(args):
    """
    Get the user's OAuth2 token.
    If we don't find one, then generate one.
    """
    try:
        with open(pdbox.TOKEN_PATH) as f:
            pdbox.debug("Using token from file", args)
            token = f.read()
    except:
        pdbox.debug("Generating new token", args)
        try:
            token = auth_flow(args)
        except Exception as e:
            pdbox.debug(e, args)
            fail("Authentication failed; exiting", args)
    return token


def login(token):
    """Log in to the Dropbox client."""
    pdbox.dbx = dropbox.Dropbox(token, timeout=None)


def auth_flow(args):
    """
    Get an auth code from the user, then send it to an API Gateway endpoint to
    authorize with the app.
    """
    auth_url = "https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=kkdoudk5jlebl37"  # noqa
    endpoint = "https://jrqx349ulj.execute-api.us-east-1.amazonaws.com/pdbox/auth"  # noqa

    print("1. Go to: %s" % auth_url)
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")

    prompt = "Enter the authorization code here: "
    try:
        try:
            code = raw_input(prompt).strip()
        except NameError:
            code = input(prompt).strip()
    except KeyboardInterrupt:
        print("")
        fail("Cancelled", args)

    response = requests.get("%s?c=%s" % (endpoint, code))
    if response.status_code != 200 or response.text == "server error":
        fail("Authorization failed", args)

    token = response.text
    if not os.path.exists(os.path.dirname(pdbox.TOKEN_PATH)):
        os.makedirs(os.path.dirname(pdbox.TOKEN_PATH))
    with open(pdbox.TOKEN_PATH, "w") as f:
        f.write(token)
        pdbox.debug("Created new token at %s" % pdbox.TOKEN_PATH, args)

    return token
