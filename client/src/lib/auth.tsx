import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User, signInWithPopup, signOut as firebaseSignOut } from "firebase/auth";
import { auth, googleProvider } from "./firebase";
import { useToast } from "../hooks/use-toast";
import { useLocation } from "wouter";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();
  const [, setLocation] = useLocation();

  useEffect(() => {
    // In development, set a mock user
    if (import.meta.env.DEV) {
      setUser({
        email: 'dev@agile6.com',
        emailVerified: true,
        displayName: 'Development User',
      } as User);
      setLoading(false);
      return;
    }

    try {
      const unsubscribe = auth.onAuthStateChanged((user) => {
        setUser(user);
        setLoading(false);
        // Redirect to home page if user is authenticated and we're on the login page
        if (user && window.location.pathname === "/login") {
          setLocation("/");
        } else if (!user && window.location.pathname !== "/login") {
          setLocation("/login");
        }
      }, (error) => {
        console.error('Auth state change error:', error);
        setLoading(false);
        toast({
          title: "Authentication Error",
          description: "There was an error with the authentication service. Please try again later.",
          variant: "destructive",
        });
      });

      return () => unsubscribe();
    } catch (error) {
      console.error('Auth initialization error:', error);
      setLoading(false);
      toast({
        title: "Authentication Error",
        description: "Failed to initialize authentication service. Please check your configuration.",
        variant: "destructive",
      });
    }
  }, [setLocation, toast]);

  const handleSignIn = async () => {
    // In development, skip actual authentication
    if (import.meta.env.DEV) {
      setUser({
        email: 'dev@agile6.com',
        emailVerified: true,
        displayName: 'Development User',
      } as User);
      setLocation("/");
      return;
    }

    try {
      const result = await signInWithPopup(auth, googleProvider);
      if (!result.user.email?.endsWith('@agile6.com')) {
        await firebaseSignOut(auth);
        toast({
          title: "Authentication Error",
          description: "Only @agile6.com email addresses are allowed.",
          variant: "destructive",
        });
        return;
      }
      toast({
        title: "Welcome!",
        description: "Successfully signed in.",
      });
      setLocation("/");
    } catch (error: any) {
      console.error('Sign in error:', error);
      let errorMessage = "An error occurred during sign in. Please try again.";
      if (error.code === 'auth/configuration-not-found') {
        errorMessage = "Firebase configuration error. Please check your setup.";
      } else if (error.code === 'auth/popup-blocked') {
        errorMessage = "Pop-up was blocked by your browser. Please allow pop-ups for this site.";
      }
      toast({
        title: "Authentication Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleSignOut = async () => {
    try {
      await firebaseSignOut(auth);
      setLocation("/login");
      toast({
        title: "Signed out",
        description: "Successfully signed out.",
      });
    } catch (error: any) {
      console.error('Sign out error:', error);
      toast({
        title: "Error",
        description: "Failed to sign out. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signIn: handleSignIn,
        signOut: handleSignOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}