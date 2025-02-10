import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import RepoForm from "@/components/repository/repo-form";
import ProcessingStatus from "@/components/repository/processing-status";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { useMutation } from "@tanstack/react-query";

export default function RepositoryProcessor() {
  const { toast } = useToast();

  const processRepo = useMutation({
    mutationFn: async (url: string) => {
      const response = await apiRequest("POST", "/api/repositories", {
        url,
        status: "pending",
      });
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Repository submitted",
        description: "The repository is being processed.",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to process repository.",
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
