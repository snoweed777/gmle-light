import { useState, useRef, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ingestApi, UploadResponse, UploadedFileInfo, IngestHistoryItem } from "@/api/ingest";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorAlert from "@/components/ErrorAlert";
import { Upload, FileText, Calendar, History } from "lucide-react";

export default function IngestPage() {
  const { spaceId } = useParams<{ spaceId: string }>();
  const [file, setFile] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<UploadResponse | null>(null);
  const [selectedFileInfo, setSelectedFileInfo] = useState<UploadedFileInfo | null>(null);
  const [title, setTitle] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: filesData, isLoading: filesLoading } = useQuery({
    queryKey: ["uploadedFiles", spaceId],
    queryFn: async () => {
      if (!spaceId) throw new Error("Space ID is required");
      return ingestApi.listFiles(spaceId);
    },
    enabled: !!spaceId,
  });

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ["ingestHistory", spaceId],
    queryFn: async () => {
      if (!spaceId) throw new Error("Space ID is required");
      return ingestApi.getHistory(spaceId);
    },
    enabled: !!spaceId,
  });

  const uploadMutation = useMutation({
    mutationFn: async (data: { file: File }) => {
      if (!spaceId) throw new Error("Space ID is required");
      return ingestApi.upload(spaceId, data.file);
    },
    onSuccess: (data) => {
      setUploadedFile(data);
      setFile(null);
      setSelectedFileInfo(null);
      if (!title) {
        setTitle(data.filename.replace(/\.[^/.]+$/, ""));
      }
      queryClient.invalidateQueries({ queryKey: ["uploadedFiles", spaceId] });
    },
  });

  const [currentIngestId, setCurrentIngestId] = useState<string | null>(null);
  const [completedIngestStatus, setCompletedIngestStatus] = useState<IngestResponse | null>(null);

  const ingestMutation = useMutation({
    mutationFn: async (data: { filePath: string; title?: string }) => {
      if (!spaceId) throw new Error("Space ID is required");
      const response = await ingestApi.ingest(spaceId, data.filePath, data.title);
      setCurrentIngestId(response.ingest_id);
      setCompletedIngestStatus(null); // Clear previous result
      return response;
    },
    onSuccess: () => {
      // Don't clear state immediately - wait for status check
    },
  });

  // Poll ingest status
  const { data: ingestStatus, isLoading: isPolling } = useQuery({
    queryKey: ["ingestStatus", spaceId, currentIngestId],
    queryFn: async () => {
      if (!spaceId || !currentIngestId) return null;
      return ingestApi.getStatus(spaceId, currentIngestId);
    },
    enabled: !!currentIngestId && !!spaceId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Poll every 2 seconds if still processing
      if (!data) return 2000; // Initial poll
      return data.status === "processing" ? 2000 : false;
    },
  });

  // Update UI when ingest completes
  useEffect(() => {
    if (ingestStatus?.status === "completed") {
      setCompletedIngestStatus(ingestStatus);
      // Clear form state after a delay to show the result
      setTimeout(() => {
        setUploadedFile(null);
        setSelectedFileInfo(null);
        setTitle("");
        setCurrentIngestId(null);
        queryClient.invalidateQueries({ queryKey: ["uploadedFiles", spaceId] });
        queryClient.invalidateQueries({ queryKey: ["ingestHistory", spaceId] });
      }, 5000); // Show result for 5 seconds before clearing
    }
  }, [ingestStatus, queryClient, spaceId]);

  const validateFile = (selectedFile: File): boolean => {
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (ext !== "txt" && ext !== "docx") {
      alert("対応形式: .txt, .docx");
      return false;
    }
    return true;
  };

  const handleFileSelect = (selectedFile: File) => {
    if (!validateFile(selectedFile)) return;
    setFile(selectedFile);
    if (!title) {
      setTitle(selectedFile.name.replace(/\.[^/.]+$/, ""));
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!uploadMutation.isPending && !uploadedFile) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (uploadMutation.isPending || uploadedFile) return;

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDropAreaClick = () => {
    if (!uploadMutation.isPending && !uploadedFile) {
      fileInputRef.current?.click();
    }
  };

  const handleUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !spaceId) return;
    uploadMutation.mutate({ file });
  };

  const handleIngest = () => {
    if (!spaceId) return;
    const filePath = uploadedFile?.file_path || selectedFileInfo?.file_path;
    if (!filePath) return;
    ingestMutation.mutate({
      filePath,
      title: title || undefined,
    });
  };

  const handleSelectExistingFile = (fileInfo: UploadedFileInfo) => {
    setSelectedFileInfo(fileInfo);
    setUploadedFile(null);
    setFile(null);
    if (!title) {
      setTitle(fileInfo.filename.replace(/\.[^/.]+$/, ""));
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateString: string): string => {
    // Ensure UTC interpretation if timezone info is missing
    const dateStr = dateString.endsWith("Z") || dateString.includes("+") || dateString.includes("-", 10)
      ? dateString
      : `${dateString}Z`; // Add Z to indicate UTC if no timezone info
    return new Intl.DateTimeFormat("ja-JP", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZone: "Asia/Tokyo",
    }).format(new Date(dateStr));
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Ingest - {spaceId}</h1>
        <Link to={`/spaces/${spaceId}`}>
          <Button variant="outline">Back to Space</Button>
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload File</CardTitle>
              <CardDescription>
                Upload a text file (.txt) or Word document (.docx)
              </CardDescription>
            </CardHeader>
          <CardContent>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">File</label>
                <Input
                  ref={fileInputRef}
                  type="file"
                  accept=".txt,.docx"
                  onChange={handleFileChange}
                  disabled={uploadMutation.isPending || !!uploadedFile}
                  className="hidden"
                />
                <div
                  onClick={handleDropAreaClick}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  className={`
                    relative border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                    transition-colors duration-200
                    ${
                      isDragging
                        ? "border-primary bg-primary/5"
                        : "border-muted-foreground/25 hover:border-primary/50"
                    }
                    ${uploadMutation.isPending || uploadedFile ? "opacity-50 cursor-not-allowed" : ""}
                  `}
                >
                  <Upload
                    className={`mx-auto h-12 w-12 mb-4 ${
                      isDragging ? "text-primary" : "text-muted-foreground"
                    }`}
                  />
                  {file ? (
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        {file.name}
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        クリックして別のファイルを選択
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm font-medium text-foreground mb-1">
                        ファイルをドラッグ&ドロップ
                      </p>
                      <p className="text-xs text-muted-foreground">
                        またはクリックしてファイルを選択
                      </p>
                      <p className="text-xs text-muted-foreground mt-2">
                        対応形式: .txt, .docx
                      </p>
                    </div>
                  )}
                </div>
                {uploadedFile && (
                  <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded">
                    <p className="text-sm font-medium text-green-800">
                      ✓ Uploaded: {uploadedFile.filename}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      {(uploadedFile.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                )}
              </div>
              <Button
                type="submit"
                disabled={!file || uploadMutation.isPending || !!uploadedFile || !!selectedFileInfo}
                className="w-full"
              >
                {uploadMutation.isPending ? (
                  <>
                    <LoadingSpinner size="sm" className="mr-2" />
                    Uploading...
                  </>
                ) : (
                  "Upload"
                )}
              </Button>
            </form>
            {(uploadedFile || selectedFileInfo) && (
              <div className="mt-4 pt-4 border-t space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Title (optional)
                  </label>
                  <Input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Source title"
                    disabled={ingestMutation.isPending}
                  />
                </div>
                <Button
                  onClick={handleIngest}
                  disabled={ingestMutation.isPending || (!uploadedFile && !selectedFileInfo)}
                  className="w-full"
                >
                  {ingestMutation.isPending ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Ingesting...
                    </>
                  ) : (
                    "Ingest"
                  )}
                </Button>
              </div>
            )}
          </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Existing Files</CardTitle>
              <CardDescription>
                Select an existing file to ingest
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filesLoading ? (
                <div className="flex items-center justify-center py-8">
                  <LoadingSpinner size="sm" />
                </div>
              ) : filesData && filesData.files.length > 0 ? (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {filesData.files.map((fileInfo) => (
                    <div
                      key={fileInfo.file_path}
                      onClick={() => handleSelectExistingFile(fileInfo)}
                      className={`
                        p-3 border rounded-lg cursor-pointer transition-colors
                        ${
                          selectedFileInfo?.file_path === fileInfo.file_path
                            ? "border-primary bg-primary/5"
                            : "border-muted-foreground/25 hover:border-primary/50"
                        }
                        ${ingestMutation.isPending ? "opacity-50 cursor-not-allowed" : ""}
                      `}
                    >
                      <div className="flex items-start gap-3">
                        <FileText className="h-5 w-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">
                            {fileInfo.filename}
                          </p>
                          <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                            <span>{formatFileSize(fileInfo.size)}</span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {formatDate(fileInfo.modified_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No files uploaded yet
                </p>
              )}
              {selectedFileInfo && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm font-medium mb-2">Selected:</p>
                  <p className="text-sm text-muted-foreground">
                    {selectedFileInfo.filename}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent>
            {(uploadMutation.isError || ingestMutation.isError) && (
              <ErrorAlert
                title={
                  uploadMutation.isError ? "Upload failed" : "Ingest failed"
                }
                message={
                  (uploadMutation.error || ingestMutation.error) instanceof Error
                    ? (uploadMutation.error || ingestMutation.error)?.message || "Unknown error"
                    : "Unknown error"
                }
              />
            )}
            {(ingestMutation.isPending || (ingestStatus?.status === "processing" && !completedIngestStatus)) && (
              <div className="flex flex-col items-center justify-center py-8 space-y-2">
                <LoadingSpinner size="lg" />
                <p className="text-sm text-muted-foreground">Ingesting...</p>
                {isPolling && (
                  <p className="text-xs text-muted-foreground mt-1">Checking status...</p>
                )}
              </div>
            )}
            {(completedIngestStatus || ingestStatus?.status === "completed") && (
              <div className="space-y-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">✓</span>
                  <p className="text-sm font-medium text-green-800">Ingest completed</p>
                </div>
                <div className="space-y-1 pl-6">
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium">Sources:</span> {(completedIngestStatus || ingestStatus)?.sources_count}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    <span className="font-medium">New sources:</span> {(completedIngestStatus || ingestStatus)?.new_sources_count}
                  </p>
                  {(completedIngestStatus || ingestStatus)?.filename && (
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium">File:</span> {(completedIngestStatus || ingestStatus)?.filename}
                    </p>
                  )}
                  {(completedIngestStatus || ingestStatus)?.completed_at && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Completed at: {formatDate((completedIngestStatus || ingestStatus)!.completed_at!)}
                    </p>
                  )}
                </div>
              </div>
            )}
            {ingestMutation.isSuccess && !ingestStatus && !completedIngestStatus && (
              <div className="space-y-2 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm font-medium text-blue-800">Ingest started</p>
                <p className="text-sm text-muted-foreground">
                  Processing... Please wait.
                </p>
              </div>
            )}
            {!ingestMutation.isPending &&
              !ingestMutation.isSuccess &&
              !ingestMutation.isError &&
              !ingestStatus &&
              !completedIngestStatus && (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Upload a file and click Ingest to start
                </p>
              )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Ingest History
          </CardTitle>
          <CardDescription>
            Past ingest operations and their results
          </CardDescription>
        </CardHeader>
        <CardContent>
          {historyLoading ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner size="lg" />
            </div>
          ) : historyData && historyData.ingests.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Sources</TableHead>
                  <TableHead>New Sources</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {historyData.ingests.map((item: IngestHistoryItem) => (
                  <TableRow key={item.ingest_id}>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">
                          {formatDate(item.started_at)}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.source}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {item.filename || "-"}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-medium">
                        {item.sources_count}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`text-sm font-medium ${
                          item.new_sources_count > 0
                            ? "text-green-600"
                            : "text-muted-foreground"
                        }`}
                      >
                        {item.new_sources_count}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground">
                まだ取り込み履歴がありません
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                ファイルをアップロードして取り込みを実行すると、ここに履歴が表示されます
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


