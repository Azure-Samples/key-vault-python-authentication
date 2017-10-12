# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os


class KeyVaultSampleConfig(object):
    """
    Configuration settings for use in Key Vault sample code.  Users wishing to run this sample can either set these
    values as environment values or simply update the hard-coded values below

    :ivar subscription_id: Azure subscription id for the user intending to run the sample
    :vartype subscription_id: str
    
    :ivar client_id: Azure Active Directory AppID of the Service Principle to run the sample
    :vartype client_id: str

    :ivar client_oid: Azure Active Directory Object ID of the Service Principal to run the sample
    :vartype client_oid: str

    :ivar tenant_id: Azure Active Directory tenant id of the user intending to run the sample
    :vartype tenant_id: str

    :ivar client_secret: Azure Active Directory Application Key to run the sample
    :vartype client_secret: str
    
    :ivar location: Azure regional location on which to execute the sample 
    :vartype location: str
    
    :ivar group_name: Azure resource group on which to execute the sample 
    :vartype group_name: str
    """

    def __init__(self):
        # get credential information from the environment or replace the dummy values with your client credentials
        self.subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID', '11111111-1111-1111-1111-111111111111')
        self.client_id = os.getenv('AZURE_CLIENT_ID', '22222222-2222-2222-2222-222222222222')
        self.client_oid = os.getenv('AZURE_CLIENT_OID', '33333333-3333-3333-3333-333333333333')
        self.tenant_id = os.getenv('AZURE_TENANT_ID', '44444444-4444-4444-4444-444444444444')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET', 'zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz=')
        self.location = os.getenv('AZURE_LOCATION', 'westus')
        self.group_name = os.getenv('AZURE_RESOURCE_GROUP', 'azure-sample-group')
