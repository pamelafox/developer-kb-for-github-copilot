targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the azd environment.')
param environmentName string

@description('Primary Azure region for all resources.')
param location string

@description('Azure AI Search SKU.')
@allowed([
  'basic'
  'standard'
  'standard2'
  'standard3'
])
param searchSku string = 'standard'

var tags = {
  'azd-env-name': environmentName
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module resources './resources.bicep' = {
  scope: resourceGroup
  params: {
    environmentName: environmentName
    location: location
    principalId: deployer().objectId
    searchSku: searchSku
    tags: tags
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_APP_NAME string = resources.outputs.containerAppName
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = resources.outputs.containerRegistryEndpoint
output AZURE_SEARCH_ENDPOINT string = resources.outputs.searchEndpoint
output AZURE_OPENAI_ENDPOINT string = resources.outputs.openAiEndpoint
output AZURE_AI_FOUNDRY_ENDPOINT string = resources.outputs.foundryEndpoint
output AZURE_CONTENT_UNDERSTANDING_DEPLOYMENT string = resources.outputs.contentUnderstandingDeploymentName
output AZURE_CONTENT_UNDERSTANDING_MODEL string = resources.outputs.contentUnderstandingModelName
output AZURE_STORAGE_ACCOUNT_NAME string = resources.outputs.storageAccountName
output AZURE_STORAGE_ACCOUNT_ID string = resources.outputs.storageAccountId
output SERVICE_WEB_URI string = resources.outputs.webUri
