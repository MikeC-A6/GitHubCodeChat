import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useForm } from "react-hook-form";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiRequest, queryClient } from "@/lib/queryClient";
import type { Repository, Message } from "@shared/schema";
import { SendIcon } from "lucide-react";

type ChatInterfaceProps = {
  repository: Repository;
};

export default function ChatInterface({ repository }: ChatInterfaceProps) {
  const { register, handleSubmit, reset } = useForm<{ message: string }>();

  const { data: messages } = useQuery<Message[]>({
    queryKey: [`/api/repositories/${repository.id}/messages`],
  });

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      const response = await apiRequest("POST", `/api/repositories/${repository.id}/messages`, {
        content,
        role: "user",
      });
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: [`/api/repositories/${repository.id}/messages`],
      });
      reset();
    },
  });

  return (
    <div className="space-y-4">
      <ScrollArea className="h-[500px] border rounded-lg p-4">
        <div className="space-y-4">
          {messages?.map((message) => (
            <Card key={message.id} className={message.role === "user" ? "ml-12" : "mr-12"}>
              <div className="p-3">
                <p className="text-sm">{message.content}</p>
              </div>
            </Card>
          ))}
        </div>
      </ScrollArea>

      <form
        onSubmit={handleSubmit((data) => sendMessage.mutate(data.message))}
        className="flex gap-2"
      >
        <Input
          {...register("message", { required: true })}
          placeholder="Type your message..."
        />
        <Button type="submit" size="icon">
          <SendIcon className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}