import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

const formSchema = z.object({
  url: z.string().url("Please enter a valid GitHub URL"),
});

type RepoFormProps = {
  onSubmit: (url: string) => void;
};

export default function RepoForm({ onSubmit }: RepoFormProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      url: "",
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((data) => onSubmit(data.url))} className="space-y-4">
        <FormField
          control={form.control}
          name="url"
          render={({ field }) => (
            <FormItem>
              <FormLabel>GitHub Repository URL</FormLabel>
              <FormControl>
                <Input placeholder="https://github.com/user/repo" {...field} />
              </FormControl>
            </FormItem>
          )}
        />
        <Button type="submit" className="w-full">
          Process Repository
        </Button>
      </form>
    </Form>
  );
}
