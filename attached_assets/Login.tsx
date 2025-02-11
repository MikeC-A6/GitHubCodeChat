import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { SiGoogle } from "react-icons/si";
import { useEffect } from "react";
import { useLocation } from "wouter";
import logo from "@/assets/agile6_logo_rgb (1).png";

export default function Login() {
  const { signIn, user, loading } = useAuth();
  const [, setLocation] = useLocation();

  useEffect(() => {
    if (!loading && user) {
      setLocation("/");
    }
  }, [user, loading, setLocation]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background">
        <img src={logo} alt="Agile Six Logo" className="h-8 mb-8 animate-pulse" />
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (user) {
    return null;
  }

  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center bg-background p-4">
      <div className="w-full max-w-md flex flex-col items-center mb-8">
        <img src={logo} alt="Agile Six Logo" className="h-12 mb-4" />
        <h1 className="text-xl font-medium text-muted-foreground mb-2">GitHub Repository to Text Tool</h1>
      </div>
      
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <CardTitle className="text-2xl font-semibold">Welcome Back</CardTitle>
          <CardDescription className="text-base">
            Sign in with your Agile Six account to continue
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            size="lg"
            className="w-full h-12 text-base transition-all hover:scale-[1.02]"
            onClick={signIn}
          >
            <SiGoogle className="mr-2 h-5 w-5" />
            Continue with Google
          </Button>
          <div className="mt-4 text-center text-sm text-muted-foreground">
            By continuing, you agree to Agile Six's Terms of Service and Privacy Policy
          </div>
        </CardContent>
      </Card>

      <footer className="fixed bottom-0 w-full p-4 text-center text-sm text-muted-foreground bg-background/80 backdrop-blur-sm">
        © {new Date().getFullYear()} Agile Six. All rights reserved.
      </footer>
    </div>
  );
}
