import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eye, EyeOff } from "lucide-react";
import { LLMProviderInfo } from "@/api/llm";
import { llmDescriptions } from "@/lib/config-descriptions";

interface LLMProviderCardProps {
  name: string;
  provider: LLMProviderInfo;
  apiKey: string;
  showApiKey: boolean;
  selectedModel: string;
  onApiKeyChange: (value: string) => void;
  onShowApiKeyToggle: () => void;
  onModelChange: (value: string) => void;
}

export default function LLMProviderCard({
  name,
  provider,
  apiKey,
  showApiKey,
  selectedModel,
  onApiKeyChange,
  onShowApiKeyToggle,
  onModelChange,
}: LLMProviderCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="capitalize">{name} Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-1 block">API Key</label>
          <p className="text-xs text-muted-foreground mb-2">
            {llmDescriptions.api_key.description}
          </p>
          <div className="flex gap-2">
            <Input
              type={showApiKey ? "text" : "password"}
              placeholder={provider.api_key_configured ? "••••••••••••••••" : "Enter API key"}
              value={apiKey}
              onChange={(e) => onApiKeyChange(e.target.value)}
            />
            <Button variant="outline" size="icon" onClick={onShowApiKeyToggle}>
              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        <div>
          <label className="text-sm font-medium mb-1 block">Model</label>
          <p className="text-xs text-muted-foreground mb-2">
            {llmDescriptions.default_model.description}
          </p>
          <select
            className="w-full px-3 py-2 border rounded-md"
            value={selectedModel}
            onChange={(e) => onModelChange(e.target.value)}
          >
            {provider.available_models.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium mb-1 block">API URL</label>
          <p className="text-xs text-muted-foreground mb-2">
            {llmDescriptions.api_url.description}
          </p>
          <Input value={provider.api_url} disabled className="bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}

