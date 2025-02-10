import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import RepoForm from "@/components/repository/repo-form";
import ProcessingStatus from "@/components/repository/processing-status";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { useMutation, useQueryClient } from "@tanstack/react-query";

export default function RepositoryProcessor() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const processRepo = useMutation({
    mutationFn: async (url: string) => {
      try {
        const response = await apiRequest("POST", "/api/github/process", {
          url,
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Failed to process repository: ${errorText}`);
        }

        return response.json();
      } catch (error) {
        console.error('Error processing repository:', error);
        throw error;
      }
    },
    onSuccess: () => {
      toast({
        title: "Repository submitted",
        description: "The repository is being processed.",
      });
      // Refresh the repositories list
      queryClient.invalidateQueries({ queryKey: ["/api/github/repositories"] });
    },
    onError: (error: Error) => {
      toast({
        title: "Error",
        description: error.message || "Failed to process repository.",
        variant: "destructive",
      });
    },
  });

  return (
    <div className="max-w-3xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Repository Processor</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <RepoForm onSubmit={(url) => processRepo.mutate(url)} />
          <ProcessingStatus />
        </CardContent>
      </Card>
    </div>
  );
}
