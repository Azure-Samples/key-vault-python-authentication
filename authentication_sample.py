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
from azure.keyvault import KeyVaultClient


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

        credentials = ServicePrincipalCredentials(client_id=self.config.client_id,
                                                  secret=self.config.client_secret,
                                                  tenant=self.config.tenant_id)

        client = KeyVaultClient(credentials)

        client.set_secret(vault.properties.vault_uri, 'auth-sample-secret', 'vault is authenticated')

        client.get_secret(vault.properties.vault_uri, 'auth-sample-secret')


if __name__ == "__main__":
    run_all_samples([AuthenticationSample()])