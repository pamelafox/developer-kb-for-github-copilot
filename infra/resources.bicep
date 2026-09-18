targetScope = 'resourceGroup'

param environmentName string
param location string
param tags object
param searchSku string
param principalId string

param chatDeployment object = {
  name: 'gpt-5.4-mini'
  model: 'gpt-5.4-mini'
  version: '2026-03-17'
  capacity: 100
}
param embeddingDeployment object = {
  name: 'text-embedding-3-large'
  model: 'text-embedding-3-large'
  version: '1'
  capacity: 30
}

var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))
var searchServiceContributorRoleId = '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
var searchIndexDataContributorRoleId = '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
var cognitiveServicesUserRoleId = 'a97b65f3-24c7-4388-baec-2e87135dc908'
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
var storageBlobDataContributorRoleId = 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
var storageBlobDataReaderRoleId = '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'log-${resourceToken}'
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: 'cae-${resourceToken}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'cr${resourceToken}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-kb-${resourceToken}'
  location: location
  tags: tags
}

resource aiAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: 'ai-${resourceToken}'
  location: location
  tags: tags
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: 'ai-${resourceToken}'
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
      virtualNetworkRules: []
      ipRules: []
    }
  }

  resource chat 'deployments' = {
    name: chatDeployment.name
    sku: {
      name: 'GlobalStandard'
      capacity: chatDeployment.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: chatDeployment.model
        version: chatDeployment.version
      }
    }
  }

  resource embedding 'deployments' = {
    name: embeddingDeployment.name
    dependsOn: [
      chat
    ]
    sku: {
      name: 'GlobalStandard'
      capacity: embeddingDeployment.capacity
    }
    properties: {
      model: {
        format: 'OpenAI'
        name: embeddingDeployment.model
        version: embeddingDeployment.version
      }
    }
  }
}

resource search 'Microsoft.Search/searchServices@2025-05-01' = {
  name: 'srch-${resourceToken}'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: searchSku
  }
  properties: {
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    hostingMode: 'Default'
    partitionCount: 1
    publicNetworkAccess: 'enabled'
    replicaCount: 1
    semanticSearch: 'standard'
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: 'st${resourceToken}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = {
  parent: storage
  name: 'default'

  resource corpusContainer 'containers' = {
    name: 'knowledge'
    properties: {
      publicAccess: 'None'
    }
  }

  resource extractedImagesContainer 'containers' = {
    name: 'extracted-images'
    properties: {
      publicAccess: 'None'
    }
  }

  resource styleGuideContainer 'containers' = {
    name: 'engineering-practices'
    properties: {
      publicAccess: 'None'
    }
  }

  resource styleGuideImagesContainer 'containers' = {
    name: 'engineering-practice-images'
    properties: {
      publicAccess: 'None'
    }
  }
}

resource appSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, appIdentity.id, searchServiceContributorRoleId)
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
  }
}

resource appSearchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, appIdentity.id, searchIndexDataContributorRoleId)
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
  }
}

resource provisionerSearchServiceContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, principalId, searchServiceContributorRoleId)
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchServiceContributorRoleId)
  }
}

resource provisionerSearchIndexDataContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: search
  name: guid(search.id, principalId, searchIndexDataContributorRoleId)
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', searchIndexDataContributorRoleId)
  }
}

resource searchModelUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: aiAccount
  name: guid(aiAccount.id, search.id, cognitiveServicesUserRoleId)
  properties: {
    principalId: search.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', cognitiveServicesUserRoleId)
  }
}

resource searchStorageBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, search.id, storageBlobDataContributorRoleId)
  properties: {
    principalId: search.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
  }
}

resource provisionerStorageBlobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, principalId, storageBlobDataContributorRoleId)
  properties: {
    principalId: principalId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
  }
}

resource appStorageBlobReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storage
  name: guid(storage.id, appIdentity.id, storageBlobDataReaderRoleId)
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataReaderRoleId)
  }
}

resource appRegistryPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: registry
  name: guid(registry.id, appIdentity.id, acrPullRoleId)
  properties: {
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

resource web 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-kb-${resourceToken}'
  location: location
  tags: union(tags, {
    'azd-service-name': 'web'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registry.properties.loginServer
          identity: appIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'web'
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            {
              name: 'RUNNING_IN_PRODUCTION'
              value: 'true'
            }
            {
              name: 'AZURE_CLIENT_ID'
              value: appIdentity.properties.clientId
            }
            {
              name: 'AZURE_SEARCH_ENDPOINT'
              value: 'https://${search.name}.search.windows.net'
            }
            {
              name: 'AZURE_STORAGE_ACCOUNT_NAME'
              value: storage.name
            }
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: 'https://${aiAccount.name}.openai.azure.com'
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT'
              value: chatDeployment.name
            }
            {
              name: 'AZURE_OPENAI_CHAT_MODEL'
              value: chatDeployment.model
            }
            {
              name: 'AZURE_CONTENT_UNDERSTANDING_DEPLOYMENT'
              value: chatDeployment.name
            }
            {
              name: 'AZURE_CONTENT_UNDERSTANDING_MODEL'
              value: chatDeployment.model
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: embeddingDeployment.name
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_MODEL'
              value: embeddingDeployment.model
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 4
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
  dependsOn: [
    appRegistryPull
    appSearchServiceContributor
    appSearchIndexDataContributor
    searchModelUser
    aiAccount::chat
    aiAccount::embedding
  ]
}

output containerAppName string = web.name
output containerRegistryEndpoint string = registry.properties.loginServer
output searchEndpoint string = 'https://${search.name}.search.windows.net'
output openAiEndpoint string = 'https://${aiAccount.name}.openai.azure.com'
output foundryEndpoint string = 'https://${aiAccount.name}.services.ai.azure.com'
output contentUnderstandingDeploymentName string = chatDeployment.name
output contentUnderstandingModelName string = chatDeployment.model
output storageAccountName string = storage.name
output storageAccountId string = storage.id
output webUri string = 'https://${web.properties.configuration.ingress.fqdn}'
