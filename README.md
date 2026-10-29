# Building a developer knowledge base for GitHub Copilot

You are an engineer working for **Cocoarynth**, a fictional single-origin chocolate manufacturer. Your team builds **Cocoarynth Trace**, an application that traces chocolate from cacao harvest through production and shipment.

You will begin with the project code, then connect GitHub Copilot to live GitHub artifacts through GitHub MCP. Your instructor may present additional material between exercises.

Instructors can use the [instructor guide](README.instructor.md) for deployment, local development, and testing instructions.

## Workshop exercises

1. [Exercise 1: Explore the local code](exercise1.md)
2. [Exercise 2: Add GitHub context](exercise2.md)
3. [Exercise 3: Add document context](exercise3.md)
4. [Exercise 4: Use a multi-source knowledge base](exercise4.md)

Open only the exercise your instructor asks you to complete.

## Deploy it yourself

After the workshop environment expires, deploy your own copy to keep using exercises 3 and 4. You need:

- A GitHub account with GitHub Copilot access
- An Azure subscription with quota for `gpt-5.4-mini`, `text-embedding-3-large`, Azure AI Search Standard, and Azure Container Apps
- [Azure Developer CLI](https://aka.ms/azd) 1.33 or later, [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), and [uv](https://docs.astral.sh/uv/)

Deploy the portal, ingest the sample documents, and create the three knowledge bases:

```shell
azd auth login
azd env new <environment-name> --location <region>
azd up
```

Wherever the exercises mention the provided portal URL or secrets URL, use your own values:

- **Portal URL:** `azd env get-value SERVICE_WEB_URI`
- **MCP endpoints:** listed in your portal
- **Search query key:**

  ```shell
  az login
  az search query-key list \
    --resource-group "$(azd env get-value AZURE_RESOURCE_GROUP)" \
    --service-name "$(azd env get-value AZURE_SEARCH_ENDPOINT | sed -E 's#https://([^.]+)\..*#\1#')" \
    --query "[0].key" --output tsv
  ```

When you finish, delete the Azure resources with `azd down --purge`.
