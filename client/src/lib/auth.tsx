import { createContext, useContext, ReactNode } from "react";

// Simplified mock user type
interface User {
  email: string;
  displayName: string;
}

interface AuthContextType {
  user: User;
  loading: boolean;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const mockUser: User = {
  email: 'user@example.com',
  displayName: 'Demo User',
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  // Mock auth methods that do nothing
  const handleSignIn = async () => {
    console.log('Mock sign in');
  };

  const handleSignOut = async () => {
    console.log('Mock sign out');
  };

  return (
    <AuthContext.Provider
      value={{
        user: mockUser,
        loading: false,
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