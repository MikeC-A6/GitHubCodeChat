import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import type { Repository } from "@shared/schema";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { X } from "lucide-react";

interface Props {
  value: Repository[];
  onChange: (repos: Repository[]) => void;
}

export default function RepositorySelector({ value, onChange }: Props) {
  const { data: repositories, isLoading } = useQuery<Repository[]>({
    queryKey: ["/github/repositories"],
    queryFn: async () => {
      const response = await apiRequest("GET", "/github/repositories");
      if (!response.ok) {
        throw new Error("Failed to fetch repositories");
      }
      return response.json();
    },
  });

  const vectorizedRepos = repositories?.filter((repo) => repo.vectorized) || [];

  const handleSelect = (repoId: string) => {
    const repo = vectorizedRepos.find((r) => r.id === parseInt(repoId));
    if (!repo) return;

    // Add to selection if not already selected
    if (!value.find((r) => r.id === repo.id)) {
      onChange([...value, repo]);
    }
  };

  const handleRemove = (repoId: number) => {
    onChange(value.filter((r) => r.id !== repoId));
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Select Repositories</Label>
        <Select
          disabled={isLoading || !vectorizedRepos.length}
          onValueChange={handleSelect}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select repositories to chat with..." />
          </SelectTrigger>
          <SelectContent>
            <ScrollArea className="h-[200px]">
              {vectorizedRepos.map((repo) => (
                <SelectItem key={repo.id} value={repo.id.toString()}>
                  {repo.owner}/{repo.name}
                </SelectItem>
              ))}
            </ScrollArea>
          </SelectContent>
        </Select>
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((repo) => (
            <Badge key={repo.id} variant="secondary">
              {repo.owner}/{repo.name}
              <button
                onClick={() => handleRemove(repo.id)}
                className="ml-1 hover:text-destructive"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
