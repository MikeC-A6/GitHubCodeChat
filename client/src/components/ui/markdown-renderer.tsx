import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Add type definitions for the code component props
interface CodeProps {
  node?: any;
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  return (
    <ReactMarkdown
      className={cn(
        "prose prose-sm dark:prose-invert max-w-none",
        "prose-pre:p-0 prose-pre:bg-transparent",
        className
      )}
      remarkPlugins={[remarkGfm]}
      components={{
        code: ({ node, inline, className, children, ...props }: CodeProps) => {
          const match = /language-(\w+)/.exec(className || '');
          return !inline && match ? (
            <SyntaxHighlighter
              style={oneDark}
              language={match[1]}
              PreTag="div"
              {...props}
            >
              {String(children).replace(/\n$/, '')}
            </SyntaxHighlighter>
          ) : (
            <code className={cn("bg-muted px-1.5 py-0.5 rounded-md", className)} {...props}>
              {children}
            </code>
          );
        },
        // Override default link rendering to open in new tab
        a: ({ node, ...props }) => (
          <a 
            {...props} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          />
        ),
        // Style tables according to shadcn design
        table: ({ node, ...props }) => (
          <div className="my-4 w-full overflow-y-auto">
            <table {...props} className="w-full" />
          </div>
        ),
        th: ({ node, ...props }) => (
          <th {...props} className="border px-4 py-2 text-left font-bold" />
        ),
        td: ({ node, ...props }) => (
          <td {...props} className="border px-4 py-2" />
        )
      }}
    >
      {content}
    </ReactMarkdown>
  );
};

export default MarkdownRenderer;