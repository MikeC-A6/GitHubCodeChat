import React, { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { User, signInWithPopup, signOut } from "firebase/auth";
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
      setUser({
        email: 'dev@agile6.com',
        emailVerified: true,
        displayName: 'Development User',
      } as User);
      setLoading(false);
      return;
    }

    const unsubscribe = auth.onAuthStateChanged((user) => {
      setUser(user);
      setLoading(false);
      // Redirect to home page if user is authenticated and we're on the login page
      if (user && window.location.pathname === "/login") {
        setLocation("/");
      } else if (!user && window.location.pathname !== "/login") {
        setLocation("/login");
      }
    });

    return () => unsubscribe();
  }, [setLocation]);

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
        await auth.signOut();
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
      setLocation("/"); // Redirect after successful login
    } catch (error: any) {
      toast({
        title: "Authentication Error",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const handleSignOut = async () => {
    // In development, just clear the mock user
    if (import.meta.env.DEV) {
      setUser(null);
      setLocation("/login");
      return;
    }

    try {
      await signOut(auth);
      setLocation("/login");
      toast({
        title: "Signed out",
        description: "Successfully signed out.",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
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