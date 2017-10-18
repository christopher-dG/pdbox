import dropbox
import os


def handler(event, context):
    """
    Get an OAuth2 token for a user's Dropbox account
    from an API Gateway event.
    """
    response = {
        "isBase64Encoded": False,
        "statusCode": 500,
        "headers": {},
        "body": "server error",
    }
    code = event["queryStringParameters"]["c"]
    try:
        flow = dropbox.DropboxOAuth2FlowNoRedirect(
            os.environ["PDBOX_KEY"],
            os.environ["PDBOX_SECRET"],
        )
        flow.start()
        result = flow.finish(code)
    except Exception as e:
        print("Failure: %s" % e)
        return response
    response["statusCode"] = 200
    response["body"] = result.access_token
    return response
