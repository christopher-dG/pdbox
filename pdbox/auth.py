import os
import pdbox
import requests

from pdbox.utils import fail, input_compat


def get_token():
    """
    Get the user's OAuth2 token.
    If we don't find one, then generate one.
    """
    try:
        with open(pdbox.TOKEN_PATH) as f:
            pdbox.debug("Using token from file")
            token = f.read()
    except Exception:  # File probably doesn't exist, so get a new token.
        pdbox.debug("Generating new token")
        try:
            token = auth_flow()
        except Exception as e:
            pdbox.debug(e)
            fail("Authentication failed; exiting")
    return token


def auth_flow():
    """
    Get an auth code from the user, then send it to an API Gateway endpoint to
    authorize with the app.
    """
    # This is what flow.start() returns, but it's static and always accessible
    # so we can just print it out before actually starting the flow.
    auth_url = "https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=kkdoudk5jlebl37"  # noqa
    endpoint = "https://jrqx349ulj.execute-api.us-east-1.amazonaws.com/pdbox/auth"  # noqa

    print("1. Go to: %s" % auth_url)
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")

    prompt = "Enter the authorization code here: "
    try:
        code = input_compat(prompt)
    except KeyboardInterrupt:
        print("")
        fail("Cancelled")

    # Call the authentication API to generate a token.
    response = requests.get("%s?c=%s" % (endpoint, code))
    if response.status_code != 200 or response.text == "server error":
        fail("Authorization failed")

    token = response.text
    # Write the token to a file.
    if not os.path.exists(os.path.dirname(pdbox.TOKEN_PATH)):
        os.makedirs(os.path.dirname(pdbox.TOKEN_PATH))
    with open(pdbox.TOKEN_PATH, "w") as f:
        f.write(token)
        pdbox.debug("Created new token at %s" % pdbox.TOKEN_PATH)

    return token
