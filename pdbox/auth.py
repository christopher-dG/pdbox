import dropbox
import os
import pdbox

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
    Get an auth code from the user, then send it to a Lambda function to
    authorize with the app.
    I wonder which is more important to hide: An app secret, or an AWS key that
    can run one Lambda function?
    Please don't abuse this key... How many identical URLs do you really need?
    """
    try:
        import boto3
    except ImportError:
        fail("boto3 must be installed for one-time authentication", args)

    client_id = "kkdoudk5jlebl37"
    auth_url = "https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=%s" % client_id  # noqa

    print("1. Go to: %s" % auth_url)
    print("2. Click 'Allow' (you might have to log in first)")
    print("3. Copy the authorization code")

    try:
        code = input("Enter the authorization code here: ").strip()
    except KeyboardInterrupt:
        print("")
        fail("Cancelled", args)

    client = boto3.client(
        "lambda",
        aws_access_key_id="<redacted>",
        aws_secret_access_key="<redacted>",
        region_name="us-east-1",
    )

    try:
        response = client.invoke(
            FunctionName="pdboxGetAuthToken",
            Payload=bytes("{\"code\": \"%s\"}" % code, "utf-8"),
        )
    except Exception as e:
        pdbox.debug(e, args)
        fail("Authorization failed", args)

    pdbox.debug("Response: %s" % response, args)
    if response["StatusCode"] != 200:
        fail("Authorization failed", args)

    # The returned token is quoted, so drop the end characters.
    token = response["Payload"].read().decode("utf-8")[1:-1]
    if not os.path.exists(os.path.dirname(pdbox.TOKEN_PATH)):
        os.makedirs(os.path.dirname(pdbox.TOKEN_PATH))
    with open(pdbox.TOKEN_PATH, "w") as f:
        f.write(token)
        pdbox.debug("Created new token at %s" % pdbox.TOKEN_PATH, args)

    pdbox.info("Authentication complete, pdbox no longer requires boto3", args)
    return token
