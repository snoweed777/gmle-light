import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { globalApi, GlobalConfigUpdateRequest } from "@/api/global";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import GlobalConfigSection from "@/components/GlobalConfigSection";
import { Save, Loader2 } from "lucide-react";

export default function GlobalConfigPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"params" | "api" | "logging" | "http" | "rate_limit">("params");
  const [params, setParams] = useState<Record<string, unknown>>({});
  const [api, setApi] = useState<Record<string, unknown>>({});
  const [logging, setLogging] = useState<Record<string, unknown>>({});
  const [http, setHttp] = useState<Record<string, unknown>>({});
  const [rateLimit, setRateLimit] = useState<Record<string, unknown>>({});

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["global-config"],
    queryFn: () => globalApi.get(),
  });

  useEffect(() => {
    if (config) {
      setParams(config.params);
      setApi(config.api);
      setLogging(config.logging);
      setHttp(config.http);
      setRateLimit(config.rate_limit || {});
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: (request: GlobalConfigUpdateRequest) => globalApi.update(request),
    onSuccess: (data) => {
      // Update local state with the response to ensure UI reflects saved values
      if (data) {
        setParams(data.params || {});
        setApi(data.api || {});
        setLogging(data.logging || {});
        setHttp(data.http || {});
        setRateLimit(data.rate_limit || {});
      }
      queryClient.invalidateQueries({ queryKey: ["global-config"] });
    },
  });

  const handleSave = () => {
    // Debug: Log the data being sent
    console.log("Saving config:", { params, api, logging, http });
    console.log("API anki ankiweb:", api?.anki?.ankiweb);
    updateMutation.mutate({
      params,
      api,
      logging,
      http,
      rate_limit: rateLimit,
    });
  };

  const handleParamsChange = (key: string, value: unknown) => {
    setParams((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleApiChange = (key: string, value: unknown) => {
    setApi((prev) => {
      // GlobalConfigSection passes the entire updated object when key is "api"
      // For nested updates (e.g., anki.ankiweb.username), the value is the entire api object
      if (key === "api" && typeof value === "object" && value !== null && !Array.isArray(value)) {
        // Deep merge to preserve other keys
        return { ...prev, ...(value as Record<string, unknown>) };
      }
      // For nested keys (e.g., "anki"), deep merge with existing value to preserve other properties
      if (typeof value === "object" && value !== null && !Array.isArray(value) && key in prev) {
        const existingValue = prev[key];
        if (typeof existingValue === "object" && existingValue !== null && !Array.isArray(existingValue)) {
          // Deep merge nested objects (e.g., ankiweb)
          const merged: Record<string, unknown> = { ...(existingValue as Record<string, unknown>) };
          for (const [subKey, subValue] of Object.entries(value as Record<string, unknown>)) {
            if (typeof subValue === "object" && subValue !== null && !Array.isArray(subValue) && 
                subKey in merged && typeof merged[subKey] === "object" && merged[subKey] !== null && 
                !Array.isArray(merged[subKey])) {
              // Deep merge nested object (e.g., ankiweb)
              merged[subKey] = { ...(merged[subKey] as Record<string, unknown>), ...(subValue as Record<string, unknown>) };
            } else {
              merged[subKey] = subValue;
            }
          }
          return {
            ...prev,
            [key]: merged,
          };
        }
      }
      // For top-level keys, update the specific key
      return {
        ...prev,
        [key]: value,
      };
    });
  };

  const handleLoggingChange = (key: string, value: unknown) => {
    setLogging((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleHttpChange = (key: string, value: unknown) => {
    setHttp((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleRateLimitChange = (key: string, value: unknown) => {
    setRateLimit((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !config) {
    return (
      <ErrorAlert
        title="Failed to load global configuration"
        message={error instanceof Error ? error.message : "Unknown error"}
      />
    );
  }


  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Global Configuration</h1>
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
          title="Failed to update global configuration"
          message={updateMutation.error?.message || "Unknown error"}
        />
      )}

      {updateMutation.isSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
          Global configuration updated successfully
          {config?.api?._anki_restart_needed && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-yellow-800">
              {config.api._message || "AnkiWebアカウント情報を更新しました。変更を反映するにはAnkiを再起動してください。"}
            </div>
          )}
        </div>
      )}

      <div className="space-y-4">
        <div className="flex gap-2 border-b">
          {(["params", "api", "logging", "http", "rate_limit"] as const).map((tab) => (
            <button
              key={tab}
              className={`px-4 py-2 font-medium capitalize ${
                activeTab === tab
                  ? "border-b-2 border-primary text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setActiveTab(tab)}
            >
              {tab === "rate_limit" ? "Rate Limit" : tab}
            </button>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="capitalize">{activeTab} Settings</CardTitle>
          </CardHeader>
          <CardContent>
            {activeTab === "params" && (
              <GlobalConfigSection
                data={params}
                onChange={handleParamsChange}
                renderType="params"
              />
            )}
            {activeTab === "api" && (
              <GlobalConfigSection data={api} onChange={handleApiChange} renderType="api" />
            )}
            {activeTab === "logging" && (
              <GlobalConfigSection
                data={logging}
                onChange={handleLoggingChange}
                renderType="logging"
              />
            )}
            {activeTab === "http" && (
              <GlobalConfigSection data={http} onChange={handleHttpChange} renderType="http" />
            )}
            {activeTab === "rate_limit" && (
              <GlobalConfigSection
                data={rateLimit}
                onChange={handleRateLimitChange}
                renderType="rate_limit"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

