using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'kb-lab')
param location = readEnvironmentVariable('AZURE_LOCATION', 'eastus2')
param searchReplicaCount = int(readEnvironmentVariable('AZURE_SEARCH_REPLICA_COUNT', '1'))
param chatDeploymentCapacity = int(readEnvironmentVariable('AZURE_CHAT_DEPLOYMENT_CAPACITY', '100'))
param embeddingDeploymentCapacity = int(readEnvironmentVariable('AZURE_EMBEDDING_DEPLOYMENT_CAPACITY', '30'))
