import React from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { GitHubLogoIcon, ChatBubbleIcon } from "@radix-ui/react-icons";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export default function Navbar() {
  const [location] = useLocation();
  const { user, signOut } = useAuth();

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-8">
            <Link href="/">
              <span className="text-xl font-bold cursor-pointer">Repository Processor</span>
            </Link>

            {user && (
              <div className="flex gap-4">
                <Link href="/">
                  <span className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer",
                    location === "/" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                  )}>
                    <GitHubLogoIcon className="h-5 w-5" />
                    Process Repository
                  </span>
                </Link>

                <Link href="/chat">
                  <span className={cn(
                    "flex items-center gap-2 px-3 py-2 rounded-md transition-colors cursor-pointer",
                    location === "/chat" ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                  )}>
                    <ChatBubbleIcon className="h-5 w-5" />
                    Chat
                  </span>
                </Link>
              </div>
            )}
          </div>

          {user && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <Button variant="outline" onClick={signOut}>
                Sign Out
              </Button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}