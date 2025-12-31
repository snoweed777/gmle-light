import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { llmApi, LLMConfigUpdateRequest } from "@/api/llm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import LLMProviderCard from "@/components/LLMProviderCard";
import { Save, Loader2, CheckCircle2 } from "lucide-react";

export default function LLMConfigPage() {
  const queryClient = useQueryClient();
  const [activeProvider, setActiveProvider] = useState<string>("cohere");
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [selectedModels, setSelectedModels] = useState<Record<string, string>>({});

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["llm-config"],
    queryFn: () => llmApi.get(),
  });

  useEffect(() => {
    if (config) {
      setActiveProvider(config.active_provider);
      const models: Record<string, string> = {};
      Object.entries(config.providers).forEach(([name, provider]) => {
        models[name] = provider.default_model;
      });
      setSelectedModels(models);
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: (request: LLMConfigUpdateRequest) => llmApi.update(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["llm-config"] });
      setApiKeys({});
    },
  });

  const handleSave = () => {
    const providerConfig: Record<string, { api_key?: string; default_model?: string }> = {};

    Object.entries(apiKeys).forEach(([provider, apiKey]) => {
      if (apiKey) {
        providerConfig[provider] = { api_key: apiKey };
      }
    });

    Object.entries(selectedModels).forEach(([provider, model]) => {
      if (model && model !== config?.providers[provider]?.default_model) {
        if (!providerConfig[provider]) {
          providerConfig[provider] = {};
        }
        providerConfig[provider].default_model = model;
      }
    });

    updateMutation.mutate({
      active_provider: activeProvider,
      provider_config: Object.keys(providerConfig).length > 0 ? providerConfig : undefined,
    });
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !config) {
    return (
      <ErrorAlert
        title="Failed to load LLM configuration"
        message={error instanceof Error ? error.message : "Unknown error"}
      />
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">LLM Configuration</h1>
        <div className="flex gap-2">
          <Link to="/">
            <Button variant="outline">Back</Button>
          </Link>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                Save
              </>
            )}
          </Button>
        </div>
      </div>

      {updateMutation.isError && (
        <ErrorAlert
          title="Failed to update LLM configuration"
          message={updateMutation.error?.message || "Unknown error"}
        />
      )}

      {updateMutation.isSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
          LLM configuration updated successfully
        </div>
      )}

      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Active LLM Provider</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {Object.entries(config.providers).map(([name, provider]) => (
              <div key={name} className="flex items-center space-x-3">
                <input
                  type="radio"
                  id={`provider-${name}`}
                  name="provider"
                  value={name}
                  checked={activeProvider === name}
                  onChange={(e) => setActiveProvider(e.target.value)}
                  className="w-4 h-4"
                />
                <label htmlFor={`provider-${name}`} className="flex items-center gap-2 cursor-pointer">
                  <span className="font-medium capitalize">{name}</span>
                  {provider.api_key_configured && (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  )}
                  {!provider.api_key_configured && (
                    <span className="text-sm text-muted-foreground">(Not configured)</span>
                  )}
                </label>
              </div>
            ))}
          </CardContent>
        </Card>

        {Object.entries(config.providers).map(([name, provider]) => (
          <LLMProviderCard
            key={name}
            name={name}
            provider={provider}
            apiKey={apiKeys[name] || ""}
            showApiKey={showApiKeys[name] || false}
            selectedModel={selectedModels[name] || provider.default_model}
            onApiKeyChange={(value) => setApiKeys({ ...apiKeys, [name]: value })}
            onShowApiKeyToggle={() => setShowApiKeys({ ...showApiKeys, [name]: !showApiKeys[name] })}
            onModelChange={(value) => setSelectedModels({ ...selectedModels, [name]: value })}
          />
        ))}
      </div>
    </div>
  );
}

