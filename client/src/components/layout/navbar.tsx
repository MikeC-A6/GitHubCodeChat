import React from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { GitHubLogoIcon, ChatBubbleIcon } from "@radix-ui/react-icons";

export default function Navbar() {
  const [location] = useLocation();

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/">
              <span className="text-xl font-bold cursor-pointer">Repository Chat</span>
            </Link>

            <div className="flex gap-4">
              <Link href="/">
                <span className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer",
                  location === "/" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                )}>
                  <ChatBubbleIcon className="h-5 w-5" />
                  Chat
                </span>
              </Link>

              <Link href="/repository">
                <span className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer",
                  location === "/repository" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                )}>
                  <GitHubLogoIcon className="h-5 w-5" />
                  Process Repository
                </span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}