from pulumi_azure_native.storage import (
    NetworkRuleSetArgs as StorageNetworkRuleSetArgs,
    DefaultAction as StorageNetworkRuleSetDefaultAction,
)

from pulumi_azure_native.keyvault import (
    NetworkRuleSetArgs as KeyVaultNetworkRuleSetArgs,
)

KEY_VAULT_DEFAULT_FIREWALL = KeyVaultNetworkRuleSetArgs(
    default_action="Allow",
    bypass="AzureServices",
    ip_rules=None,
    virtual_network_rules=None,
)

STORAGE_ACCOUNT_DEFAULT_FIREWALL = StorageNetworkRuleSetArgs(
    default_action=StorageNetworkRuleSetDefaultAction("Allow"),
    bypass="AzureServices",
    ip_rules=None,
    virtual_network_rules=None,
)
