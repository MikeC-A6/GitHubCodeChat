import React from "react";
import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import RepositoryProcessor from "@/pages/repository-processor";
import Chat from "@/pages/chat";
import Navbar from "@/components/layout/navbar";

function AppContent() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <Router />
      </main>
    </div>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/chat" component={Chat} />
      <Route path="/" component={RepositoryProcessor} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;