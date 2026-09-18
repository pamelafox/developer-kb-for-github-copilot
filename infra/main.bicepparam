using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'kb-lab')
param location = readEnvironmentVariable('AZURE_LOCATION', 'eastus2')
