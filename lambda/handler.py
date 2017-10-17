import dropbox
import os


def handler(payload, _):
    """Authenticate the app to a Dropbox account and return the token."""
    print("Code: %s" % payload["code"])

    flow = dropbox.DropboxOAuth2FlowNoRedirect(
        os.environ["PDBOX_KEY"],
        os.environ["PDBOX_SECRET"],
    )
    flow.start()

    try:
        result = flow.finish(payload["code"])
    except Exception as e:
        print("Failure: %s" % e)
        raise e
    else:
        print(result)
        return result.access_token
