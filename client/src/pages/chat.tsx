import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ChatInterface from "@/components/chat/chat-interface";
import RepositorySelector from "@/components/chat/repository-selector";
import { useState } from "react";
import type { Repository } from "@shared/schema";

export default function Chat() {
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);

  return (
    <div className="max-w-4xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Chat with Repository</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <RepositorySelector
            value={selectedRepo}
            onChange={setSelectedRepo}
          />
          {selectedRepo && (
            <ChatInterface repository={selectedRepo} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
