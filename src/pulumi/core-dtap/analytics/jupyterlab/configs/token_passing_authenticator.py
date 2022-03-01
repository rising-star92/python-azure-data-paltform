from distutils.version import LooseVersion as V
import jwt
from oauthenticator.azuread import AzureAdOAuthenticator
from tornado.httpclient import HTTPRequest
import urllib

"""
Adapted from:
- https://github.com/jupyterhub/oauthenticator/blob/main/oauthenticator/azuread.py
- https://github.com/jupyterhub/oauthenticator/blob/main/examples/auth_state/jupyterhub_config.py
"""

# pyjwt 2.0 has changed its signature,
# but mwoauth pins to pyjwt 1.x
PYJWT_2 = V(jwt.__version__) >= V("2.0")


class AzureAdTokenOAuthenticator(AzureAdOAuthenticator):
    async def authenticate(self, handler, data=None):
        code = handler.get_argument("code")

        params = dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type="authorization_code",
            code=code,
            redirect_uri=self.get_callback_url(handler),
        )

        data = urllib.parse.urlencode(params, doseq=True, encoding="utf-8", safe="=")

        url = self.token_url

        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        req = HTTPRequest(
            url,
            method="POST",
            headers=headers,
            body=data,  # Body is required for a POST...
        )

        resp_json = await self.fetch(req)

        userdict = {}
        userdict["auth_state"] = auth_state = {}
        auth_state["access_token"] = resp_json["access_token"]
        auth_state["refresh_token"] = resp_json.get("refresh_token", None)

        id_token = resp_json["id_token"]
        if PYJWT_2:
            decoded = jwt.decode(
                id_token,
                options={"verify_signature": False},
                audience=self.client_id,
            )
        else:
            # pyjwt 1.x
            decoded = jwt.decode(id_token, verify=False)

        # results in a decoded JWT for the user data
        userdict["name"] = decoded[self.username_claim]
        auth_state["user"] = decoded

        return userdict

    # define our Authenticator with `.pre_spawn_start`
    # for passing auth_state into the user environment
    async def pre_spawn_start(self, user, spawner):
        auth_state = await user.get_auth_state()

        if not auth_state:
            # user has no auth state
            return

        # define some environment variables from auth_state
        spawner.environment["AZURE_AAD_ACCESS_TOKEN"] = auth_state["access_token"]
        # spawner.environment["AZURE_AAD_REFRESH_TOKEN"] = auth_state.get("refresh_token", "")


c.JupyterHub.authenticator_class = AzureAdTokenOAuthenticator

# enable authentication state
c.AzureAdTokenOAuthenticator.enable_auth_state = True
c.AzureAdTokenOAuthenticator.refresh_pre_spawn = True
