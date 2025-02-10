import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useQuery } from "@tanstack/react-query";
import type { Repository } from "@shared/schema";

type RepositorySelectorProps = {
  value: Repository | null;
  onChange: (repo: Repository | null) => void;
};

export default function RepositorySelector({ value, onChange }: RepositorySelectorProps) {
  const { data: repositories } = useQuery<Repository[]>({
    queryKey: ["/api/repositories"],
  });

  return (
    <Select
      value={value?.id.toString()}
      onValueChange={(val) => {
        const repo = repositories?.find((r) => r.id.toString() === val) ?? null;
        onChange(repo);
      }}
    >
      <SelectTrigger>
        <SelectValue placeholder="Select a repository" />
      </SelectTrigger>
      <SelectContent>
        {repositories?.map((repo) => (
          <SelectItem key={repo.id} value={repo.id.toString()}>
            {repo.owner}/{repo.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
