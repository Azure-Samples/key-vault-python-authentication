---
services: key-vault
platforms: python
author: schaabs
---

***DISCLAIMER: The data plane samples in this repo are for `azure-keyvault`. In the interest of simplifying APIs, `azure-keyvault` and `KeyVaultClient` have been split into separate packages and clients. For samples using these latest packages, please visit:***

- [`azure-keyvault-certificates` samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/keyvault/azure-keyvault-certificates/samples)
- [`azure-keyvault-keys` samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/keyvault/azure-keyvault-keys/samples)
- [`azure-keyvault-secrets` samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/keyvault/azure-keyvault-secrets/samples)

***This repo is archived since `azure-keyvault-x` packages have become stable. For the latest management plane package, please visit [`azure-mgmt-keyvault`](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/keyvault/azure-mgmt-keyvault).***

***DISCLAIMER: If you are looking to migrate from `azure-keyvault` to `azure-keyvault-x`, we suggest getting started with the following migration guides:***

- [`azure-keyvault-certificates` migration guide](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/keyvault/azure-keyvault-certificates/migration_guide.md)
- [`azure-keyvault-keys` migration guide](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/keyvault/azure-keyvault-keys/migration_guide.md)
- [`azure-keyvault-secrets` migration guide](https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/keyvault/azure-keyvault-secrets/migration_guide.md)

# Authentication samples for Azure Key Vault using the Azure Python SDK

This Sample repo includes sample code demonstrating common mechanism for authenticating to an Azure Key Vault vault.

## Samples in this repo
* authentication_sample.py
  * auth_using_service_principle_credentials -- authenticates to an Azure Key Vault vault using AAD service principle credentials 
  * auth_using_adal_callback -- authenticates to an Azure Key Vault vault by providing a callback to authenticate using adal


## Running The samples
1. If you don't already have it, [install Python](https://www.python.org/downloads/).

2. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to run this example, but it's not mandatory. You can initialize a virtual environment this way:

    ```
    pip install virtualenv
    virtualenv mytestenv
    cd mytestenv
    source bin/activate
    ```

3. Clone the repository.

    ```
    git clone https://github.com/Azure-Samples/key-vault-python-authentication.git
    ```

4. Install the dependencies using pip.

    ```
    cd key-vault-python-authentication
    pip install -r requirements.txt
    ```

5. Create an Azure service principal, using 
[Azure CLI](http://azure.microsoft.com/documentation/articles/resource-group-authenticate-service-principal-cli/),
[PowerShell](http://azure.microsoft.com/documentation/articles/resource-group-authenticate-service-principal/)
or [Azure Portal](http://azure.microsoft.com/documentation/articles/resource-group-create-service-principal-portal/).

6. Export these environment variables into your current shell. 

    ```
    export AZURE_TENANT_ID={your tenant id}
    export AZURE_CLIENT_ID={your service principal AppID}
    export AZURE_CLIENT_OID={your service principal OID}
    export AZURE_CLIENT_SECRET={your application key}
    export AZURE_SUBSCRIPTION_ID={your subscription id}
    ```

7. Run the samples, optionally specifying a space delimited list of specific samples to run.

    ```
    python run_all_samples.py [samplename[ samplename...]]
    ```

## Minimum Requirements
Python 2.7, 3.3, or 3.4.
To install Python, please go to https://www.python.org/downloads/

## More information

* [What is Key Vault?](https://docs.microsoft.com/en-us/azure/key-vault/key-vault-whatis)
* [Get started with Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/key-vault-get-started)
* [Azure Key Vault General Documentation](https://docs.microsoft.com/en-us/azure/key-vault/)
* [Azure Key Vault REST API Reference](https://docs.microsoft.com/en-us/rest/api/keyvault/)
* [Azure SDK for Python Documentation](https://docs.microsoft.com/en-us/python/api/overview/azure/key-vault?view=azure-python)
* [Azure Active Directory Documenation](https://docs.microsoft.com/en-us/azure/active-directory/)
  
# Contributing

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information 
see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) 
with any additional questions or comments.
