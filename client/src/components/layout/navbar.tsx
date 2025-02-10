import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { GitHubLogoIcon, ChatBubbleIcon } from "@radix-ui/react-icons";

export default function Navbar() {
  const [location] = useLocation();

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center gap-8">
          <Link href="/">
            <a className="text-xl font-bold">Repository Processor</a>
          </Link>
          
          <div className="flex gap-4">
            <Link href="/">
              <a className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md transition-colors",
                location === "/" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
              )}>
                <GitHubLogoIcon className="h-5 w-5" />
                Process Repository
              </a>
            </Link>
            
            <Link href="/chat">
              <a className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md transition-colors",
                location === "/chat" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
              )}>
                <ChatBubbleIcon className="h-5 w-5" />
                Chat
              </a>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
