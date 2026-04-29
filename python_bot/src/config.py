"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.
"""

class Config:
    """Agent Configuration"""

    def __init__(self, env):
        self.PORT = 3978
        # These are optional for dummy client testing
        self.azure_openai_api_key = env.get("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_deployment_name = env.get("AZURE_OPENAI_DEPLOYMENT_NAME", "")
        self.azure_openai_endpoint = env.get("AZURE_OPENAI_ENDPOINT", "")
