import React from "react";
import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import RepositoryProcessor from "@/pages/repository-processor";
import Chat from "@/pages/chat";
import Navbar from "@/components/layout/navbar";
import Login from "@/pages/Login";
import { AuthProvider, useAuth } from "@/lib/auth";
import { useEffect } from "react";

function AppContent() {
  const { user, loading } = useAuth();
  const [, setLocation] = useLocation();

  // Redirect to chat page after successful login
  useEffect(() => {
    if (!loading && user) {
      setLocation("/chat");
    }
  }, [loading, user, setLocation]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <Router />
      </main>
    </div>
  );
}

function PrivateRoute({ component: Component }: { component: React.ComponentType }) {
  const { user, loading } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!loading && !user) {
      setLocation("/login");
    }
  }, [loading, user, setLocation]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return user ? <Component /> : null;
}

function Router() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      <Route path="/chat" component={() => <PrivateRoute component={Chat} />} />
      <Route path="/" component={() => <PrivateRoute component={RepositoryProcessor} />} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <AppContent />
        <Toaster />
      </QueryClientProvider>
    </AuthProvider>
  );
}

export default App;