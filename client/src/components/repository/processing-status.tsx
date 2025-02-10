import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { Repository } from "@shared/schema";
import { apiRequest } from "@/lib/queryClient";

export default function ProcessingStatus() {
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
    // Disable retries and automatic refetching
    retry: false,
    refetchInterval: false,
    refetchOnWindowFocus: false,
    staleTime: 0,
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
                <div>
                  <h3 className="font-semibold">{repo.name}</h3>
                  <p className="text-sm text-gray-500">{repo.status}</p>
                </div>
                {repo.status === 'processing' && (
                  <Progress value={100} className="w-[100px]" />
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
