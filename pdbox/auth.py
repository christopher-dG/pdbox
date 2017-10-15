import dropbox
import os
import pdbox

APP_KEY = "kkdoudk5jlebl37"


def auth_flow():
    """Generate an OAuth2 access token."""
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(APP_KEY, get_secret())
    print("1. Go to: %s" % auth_flow.start())
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")
    auth_code = input("Enter the authorization code here: ").strip()
    token = auth_flow.finish(auth_code).access_token
    os.makedirs(os.path.dirname(pdbox.TOKEN_PATH), exist_ok=True)
    with open(pdbox.TOKEN_PATH, "w") as f:
        f.write(token)
        pdbox.debug("Created new token at %s" % pdbox.TOKEN_PATH)
    return token


def get_secret():
    """Get the app secret."""
    # TODO: Actually solve this so that other people can use it.
    return os.environ["APP_SECRET"]


def get_token():
    """
    Get the user's OAuth2 token.
    Look for an environment variable first, then check for a dedicated file.
    If we don't find one, then generate one.
    """
    if "PDBOX_TOKEN" in os.environ:
        pdbox.debug("Using token from environment variable")
        token = os.environ["PDBOX_TOKEN"]
    else:
        try:
            with open(pdbox.TOKEN_PATH) as f:
                pdbox.debug("Using token from file")
                token = f.read()
        except FileNotFoundError:
            pdbox.debug("Generating new token")
            try:
                token = pdbox.auth.auth_flow()
            except Exception as e:
                pdbox.util.fail("%s\nAuthentication failed; exiting" % e)
    return token


def login(token):
    pdbox.dbx = dropbox.Dropbox(token)
