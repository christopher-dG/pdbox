import dropbox
import os
from . import TOKEN_PATH

APP_KEY = "kkdoudk5jlebl37"


def auth():
    """Generate an OAuth2 access token."""
    auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(APP_KEY, get_secret())
    print("1. Go to: %s" % auth_flow.start())
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")
    auth_code = input("Enter the authorization code here: ").strip()
    token = auth_flow.finish(auth_code).access_token
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    with open(TOKEN_PATH, "w") as f:
        f.write(token)
    return token


def get_secret():
    """Get the app secret."""
    # TODO: Actually solve this so that other people can use it.
    return os.environ["APP_SECRET"]
