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
        console.log('Starting repository processing for URL:', url);
        
        // Log the request details
        const requestBody = { url };
        console.log('Request body:', requestBody);
        
        const response = await apiRequest("POST", "/github/process", requestBody);
        
        console.log('Response received:', {
          status: response.status,
          statusText: response.statusText,
          headers: Object.fromEntries(response.headers.entries())
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to process repository: ${errorText}`);
        }

        const data = await response.json();
        console.log('Success response:', data);
        return data;
      } catch (error) {
        console.error('Error processing repository:', error);
        throw error;
      }
    },
    onSuccess: (data) => {
      console.log('Repository processing succeeded:', data);
      toast({
        title: "Repository submitted",
        description: "The repository is being processed.",
      });
      // Refresh the repositories list
      queryClient.invalidateQueries({ queryKey: ["/github/repositories"] });
    },
    onError: (error: Error) => {
      console.error('Repository processing failed:', error);
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
          <RepoForm onSubmit={(url) => {
            console.log('Form submitted with URL:', url);
            processRepo.mutate(url);
          }} />
          <ProcessingStatus />
        </CardContent>
      </Card>
    </div>
  );
}
