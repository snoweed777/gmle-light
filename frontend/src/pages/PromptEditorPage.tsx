import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { promptsApi, PromptsConfigUpdateRequest } from "@/api/prompts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { Save, Loader2, RotateCcw } from "lucide-react";
import { promptDescriptions } from "@/lib/config-descriptions";

export default function PromptEditorPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"stage1" | "stage2">("stage1");
  const [stage1Template, setStage1Template] = useState("");
  const [stage2Template, setStage2Template] = useState("");

  const { data: config, isLoading, error } = useQuery({
    queryKey: ["prompts-config"],
    queryFn: () => promptsApi.get(),
  });

  useEffect(() => {
    if (config) {
      setStage1Template(config.stage1_extract.template);
      setStage2Template(config.stage2_build_mcq.template);
    }
  }, [config]);

  const updateMutation = useMutation({
    mutationFn: (request: PromptsConfigUpdateRequest) => promptsApi.update(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts-config"] });
    },
  });

  const handleSave = () => {
    updateMutation.mutate({
      stage1_extract: { template: stage1Template },
      stage2_build_mcq: { template: stage2Template },
    });
  };

  const handleReset = () => {
    if (config) {
      setStage1Template(config.stage1_extract.template);
      setStage2Template(config.stage2_build_mcq.template);
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !config) {
    return (
      <ErrorAlert
        title="Failed to load prompts configuration"
        message={error instanceof Error ? error.message : "Unknown error"}
      />
    );
  }

  const currentTemplate = activeTab === "stage1" ? stage1Template : stage2Template;
  const currentTitle =
    activeTab === "stage1"
      ? promptDescriptions.stage1_extract?.label || "Stage 1: 事実抽出プロンプト"
      : promptDescriptions.stage2_build_mcq?.label || "Stage 2: MCQ生成プロンプト";

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Prompt Editor</h1>
        <div className="flex gap-2">
          <Link to="/">
            <Button variant="outline">Back</Button>
          </Link>
          <Button variant="outline" onClick={handleReset}>
            <RotateCcw className="mr-2 h-4 w-4" />
            Reset
          </Button>
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
          title="Failed to update prompts"
          message={updateMutation.error?.message || "Unknown error"}
        />
      )}

      {updateMutation.isSuccess && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-md text-sm text-green-800">
          Prompts updated successfully
        </div>
      )}

      <div className="space-y-4">
        <div className="flex gap-2 border-b">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === "stage1"
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setActiveTab("stage1")}
          >
            Stage 1: Extract Facts
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === "stage2"
                ? "border-b-2 border-primary text-primary"
                : "text-muted-foreground hover:text-foreground"
            }`}
            onClick={() => setActiveTab("stage2")}
          >
            Stage 2: Build MCQ
          </button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{currentTitle}</CardTitle>
            {activeTab === "stage1" && promptDescriptions.stage1_extract && (
              <p className="text-sm text-muted-foreground mt-2">
                {promptDescriptions.stage1_extract.description}
              </p>
            )}
            {activeTab === "stage2" && promptDescriptions.stage2_build_mcq && (
              <p className="text-sm text-muted-foreground mt-2">
                {promptDescriptions.stage2_build_mcq.description}
              </p>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Prompt Template</label>
              <Textarea
                value={currentTemplate}
                onChange={(e) =>
                  activeTab === "stage1"
                    ? setStage1Template(e.target.value)
                    : setStage2Template(e.target.value)
                }
                rows={20}
                className="font-mono text-sm"
              />
            </div>

            <div className="bg-muted p-4 rounded-md">
              <p className="text-sm font-medium mb-2">Available Variables:</p>
              <ul className="text-sm space-y-1">
                {activeTab === "stage1" ? (
                  <li>
                    <code className="bg-background px-1 rounded">{"{excerpt}"}</code> - Source text excerpt
                  </li>
                ) : (
                  <li>
                    <code className="bg-background px-1 rounded">{"{facts}"}</code> - Extracted facts JSON
                  </li>
                )}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

