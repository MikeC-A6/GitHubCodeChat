import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

interface Repository {
  id: number;
  name: string;
  url: string;
  owner: string;
  description: string | null;
  files: unknown;
  status: string;
  branch: string;
  path: string;
  processedAt: Date | null;
  vectorized: boolean;
  error_message?: string;
}

export default function ProcessingStatus() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: repositories, error, isLoading } = useQuery<Repository[]>({
    queryKey: ["/github/repositories"],
    queryFn: async () => {
      try {
        console.log('Fetching repositories...');
        const response = await apiRequest("GET", "/github/repositories");
        console.log('Repository response:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error fetching repositories:', errorText);
          throw new Error("Failed to fetch repositories");
        }
        
        const data = await response.json();
        console.log('Repositories fetched:', data);
        return data;
      } catch (error) {
        console.error("Error fetching repositories:", error);
        throw error;
      }
    },
    // Refresh every 5 seconds when there are processing repositories
    refetchInterval: (data) => {
      if (data && Array.isArray(data) && data.some(repo => repo.status === 'processing')) {
        return 5000;
      }
      return false;
    },
  });

  // Mutation for initiating embedding
  const startEmbedding = useMutation({
    mutationFn: async (repoId: number) => {
      const response = await apiRequest(
        "POST",
        `/github/repositories/${repoId}/embed`
      );
      if (!response.ok) {
        const error = await response.text();
        throw new Error(error);
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast({
        title: "Embedding Started",
        description: "The repository is being processed for embeddings.",
      });
      queryClient.invalidateQueries({ queryKey: ["/github/repositories"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to start embedding process.",
        variant: "destructive",
      });
    },
  });

  if (isLoading) {
    return <Progress value={100} className="w-full" />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load repositories. Please try again later.
        </AlertDescription>
      </Alert>
    );
  }

  if (!repositories?.length) {
    return null;
  }

  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-4">
        {repositories.map((repo: Repository) => (
          <Card key={repo.id}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-center mb-4">
                <div className="flex-1">
                  <h3 className="font-semibold">{repo.name}</h3>
                  <p className="text-sm text-gray-500">
                    Status: {repo.status}
                    {repo.error_message && (
                      <span className="text-red-500 ml-2">
                        Error: {repo.error_message}
                      </span>
                    )}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  {/* Show progress indicator when processing */}
                  {repo.status === 'processing' && (
                    <Progress value={100} className="w-[100px]" />
                  )}

                  {/* Show embed button when ready */}
                  {repo.status === 'completed' && !repo.vectorized && (
                    <Button
                      onClick={() => startEmbedding.mutate(repo.id)}
                      disabled={startEmbedding.isPending}
                      variant="secondary"
                      size="sm"
                    >
                      {startEmbedding.isPending ? "Starting..." : "Generate Embeddings"}
                    </Button>
                  )}

                  {/* Show status when vectorized */}
                  {repo.vectorized && (
                    <span className="text-sm text-green-600">
                      ✓ Embeddings Ready
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
