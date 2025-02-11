import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User, signInWithPopup, signOut as firebaseSignOut } from "firebase/auth";
import { auth, googleProvider } from "./firebase";
import { useToast } from "@/hooks/use-toast";
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
      console.log('Development mode: Setting mock user');
      setUser({
        email: 'dev@agile6.com',
        emailVerified: true,
        displayName: 'Development User',
      } as User);
      setLoading(false);
      return;
    }

    try {
      console.log('Setting up auth state listener');
      if (!auth) {
        throw new Error('Firebase auth is not initialized');
      }

      const unsubscribe = auth.onAuthStateChanged((user) => {
        console.log('Auth state changed:', { isAuthenticated: !!user });
        setUser(user);
        setLoading(false);

        // Handle navigation based on auth state
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
          description: "There was an error with the authentication service. Please check your Firebase configuration.",
          variant: "destructive",
        });
      });

      return () => unsubscribe();
    } catch (error: any) {
      console.error('Auth initialization error:', error);
      setLoading(false);
      let errorMessage = "Failed to initialize authentication service.";

      if (error.message?.includes('Firebase configuration') || error.message?.includes('Firebase auth is not initialized')) {
        errorMessage = error.message;
      }

      toast({
        title: "Authentication Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  }, [setLocation, toast]);

  const handleSignIn = async () => {
    if (import.meta.env.DEV) {
      console.log('Development mode: Setting mock user for sign in');
      setUser({
        email: 'dev@agile6.com',
        emailVerified: true,
        displayName: 'Development User',
      } as User);
      setLocation("/");
      return;
    }

    try {
      if (!auth || !googleProvider) {
        throw new Error('Firebase auth is not initialized');
      }

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
      let errorMessage = "An error occurred during sign in.";

      if (error.code === 'auth/configuration-not-found') {
        errorMessage = "Firebase configuration error. Please check your setup.";
      } else if (error.code === 'auth/popup-blocked') {
        errorMessage = "Pop-up was blocked by your browser. Please allow pop-ups for this site.";
      } else if (error.message?.includes('Firebase configuration') || error.message?.includes('Firebase auth is not initialized')) {
        errorMessage = error.message;
      }

      toast({
        title: "Authentication Error",
        description: errorMessage,
        variant: "destructive",
      });
    }
  };

  const handleSignOut = async () => {
    if (import.meta.env.DEV) {
      console.log('Development mode: Clearing mock user');
      setUser(null);
      setLocation("/login");
      return;
    }

    try {
      if (!auth) {
        throw new Error('Firebase auth is not initialized');
      }

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