import dropbox
import os
import pdbox

from pdbox.utils import fail


def auth_flow():
    """Generate an OAuth2 access token."""
    key, secret = get_app()
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(key, secret)
    print("1. Go to: %s" % auth_flow.start())
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")
    try:
        auth_code = input("Enter the authorization code here: ").strip()
    except KeyboardInterrupt:
        print()
        fail("Cancelled")
    token = auth_flow.finish(auth_code).access_token
    if not os.path.exists(os.path.dirname(pdbox.TOKEN_PATH)):
        os.makedirs(os.path.dirname(pdbox.TOKEN_PATH))
    with open(pdbox.TOKEN_PATH, "w") as f:
        f.write(token)
        pdbox.debug("Created new token at %s" % pdbox.TOKEN_PATH)
    return token


def get_app():
    """Get the app key and secret."""
    # TODO: Actually solve this so that other people can use it.
    try:
        return os.environ["PDBOX_KEY"], os.environ["PDBOX_SECRET"]
    except KeyError:
        fail("$PDBOX_KEY or $PDBOX_SECRET is not set")


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
        except:
            pdbox.debug("Generating new token")
            try:
                token = pdbox.auth.auth_flow()
            except Exception as e:
                pdbox.debug(e)
                pdbox.util.fail("Authentication failed; exiting")
    return token


def login(token):
    """Log in to the Dropbox client."""
    pdbox.dbx = dropbox.Dropbox(token, timeout=None)
