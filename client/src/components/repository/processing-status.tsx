import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Repository } from "@shared/schema";

export default function ProcessingStatus() {
  const { data: repositories } = useQuery<Repository[]>({
    queryKey: ["/api/repositories"],
  });

  if (!repositories?.length) {
    return null;
  }

  return (
    <ScrollArea className="h-[400px]">
      <div className="space-y-4">
        {repositories.map((repo) => (
          <Card key={repo.id}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-medium">{repo.owner}/{repo.name}</h3>
                <span className="capitalize text-sm bg-primary/10 px-2 py-1 rounded">
                  {repo.status}
                </span>
              </div>
              
              {repo.status === "processing" && (
                <Progress value={Math.random() * 100} className="mb-2" />
              )}
              
              <p className="text-sm text-muted-foreground">
                {repo.description || "No description available"}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </ScrollArea>
  );
}
