import dropbox
import os
from . import TOKEN_PATH

# TODO: Get the app key and secret in a secure way.
APP_KEY = os.environ["APP_KEY"]
APP_SECRET = os.environ["APP_SECRET"]


def auth():
    """Generate an OAuth2 access token."""
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)
    print("1. Go to: %s" % auth_flow.start())
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")
    auth_code = input("Enter the authorization code here: ").strip()
    token = auth_flow.finish(auth_code).access_token
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(token)
    return token
