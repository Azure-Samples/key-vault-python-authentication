# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# This script expects that the following environment vars are set, or they can be hardcoded in key_vault_sample_config, these values
# SHOULD NOT be hardcoded in any code derived from this sample:
#
# AZURE_TENANT_ID: with your Azure Active Directory tenant id or domain
# AZURE_CLIENT_ID: with your Azure Active Directory Application Client ID
# AZURE_CLIENT_OID: with your Azure Active Directory Application Client Object ID
# AZURE_CLIENT_SECRET: with your Azure Active Directory Application Secret
# AZURE_SUBSCRIPTION_ID: with your Azure Subscription Id
#
# These are read from the environment and exposed through the KeyVaultSampleConfig class. For more information please
# see the implementation in key_vault_sample_config.py


from key_vault_sample_base import KeyVaultSampleBase, keyvaultsample, get_name, run_all_samples
from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault import KeyVaultClient, KeyVaultAuthentication
from azure.keyvault import KeyVaultId


class AuthenticationSample(KeyVaultSampleBase):
    """
    A collection of samples that demonstrate authenticating with the KeyVaultClient and KeyVaultManagementClient 
    """

    @keyvaultsample
    def auth_using_service_principle_credentials(self):
        """
        authenticates to the Azure Key Vault service using AAD service principle credentials 
        """
        # create a vault to validate authentication with the KeyVaultClient
        vault = self.create_vault()

        # create the service principle credentials used to authenticate the client
        credentials = ServicePrincipalCredentials(client_id=self.config.client_id,
                                                  secret=self.config.client_secret,
                                                  tenant=self.config.tenant_id)

        # create the client using the created credentials
        client = KeyVaultClient(credentials)

        # set and get a secret from the vault to validate the client is authenticated
        print('creating secret...')
        secret_bundle = client.set_secret(vault.properties.vault_uri, 'auth-sample-secret', 'client is authenticated to the vault')
        print(secret_bundle)

        print('getting secret...')
        secret_bundle = client.get_secret(vault.properties.vault_uri, 'auth-sample-secret', secret_version=KeyVaultId.version_none)
        print(secret_bundle)

    @keyvaultsample
    def auth_using_adal_callback(self):
        """
        authenticates to the Azure Key Vault by providing a callback to authenticate using adal 
        """
        # create a vault to validate authentication with the KeyVaultClient
        vault = self.create_vault()

        import adal

        # create an adal authentication context
        auth_context = adal.AuthenticationContext('https://login.microsoftonline.com/%s' % self.config.tenant_id)

        # create a callback to supply the token type and access token on request
        def adal_callback(server, resource, scope):
            token = auth_context.acquire_token_with_client_credentials(resource=resource,
                                                                       client_id=self.config.client_id,
                                                                       client_secret=self.config.client_secret)
            return token['tokenType'], token['accessToken']

        # create a KeyVaultAuthentication instance which will callback to the supplied adal_callback
        auth = KeyVaultAuthentication(adal_callback)

        # create the KeyVaultClient using the created KeyVaultAuthentication instance
        client = KeyVaultClient(auth)

        # set and get a secret from the vault to validate the client is authenticated
        print('creating secret...')
        secret_bundle = client.set_secret(vault.properties.vault_uri, 'auth-sample-secret', 'client is authenticated to the vault')
        print(secret_bundle)

        print('getting secret...')
        secret_bundle = client.get_secret(vault.properties.vault_uri, 'auth-sample-secret', secret_version=KeyVaultId.version_none)
        print(secret_bundle)

if __name__ == "__main__":
    run_all_samples([AuthenticationSample()])
