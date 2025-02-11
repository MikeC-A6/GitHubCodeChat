import { Switch, Route, useLocation } from "wouter";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { useEffect } from "react";

// Import the logo
import logo from "./assets/agile6_logo_rgb (1).png";

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

function Layout({ children }: { children: React.ReactNode }) {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="border-b bg-background">
        <div className="container flex justify-between items-center py-4">
          <div className="logo-container">
            <img src={logo} alt="Agile Six Logo" className="h-8" />
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
      </nav>
      <main className="flex-1">
        {children}
      </main>
      <footer className="bg-background border-t py-6">
        <div className="container">
          <div className="flex justify-between items-center">
            <img src={logo} alt="Agile Six Logo" className="h-6 opacity-50" />
            <p className="text-sm text-muted-foreground">
              &copy; {new Date().getFullYear()} Agile Six. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <Layout>
        <Switch>
          <Route path="/login" component={Login} />
          <Route path="/" component={() => <PrivateRoute component={Home} />} />
          <Route component={NotFound} />
        </Switch>
      </Layout>
    </AuthProvider>
  );
}

function NotFound() {
  return (
    <div className="container py-12">
      <Card className="w-full max-w-md mx-auto">
        <CardContent className="pt-6">
          <div className="flex mb-4 gap-2">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <h1 className="text-2xl font-bold">404 Page Not Found</h1>
          </div>
          <p className="text-muted-foreground mt-4">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default App;