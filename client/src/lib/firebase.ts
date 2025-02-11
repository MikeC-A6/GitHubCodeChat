import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

declare module 'vite' {
  interface ImportMetaEnv {
    VITE_FIREBASE_API_KEY: string;
    VITE_FIREBASE_PROJECT_ID: string;
    VITE_FIREBASE_APP_ID: string;
  }
}

function validateFirebaseConfig() {
  const requiredVars = {
    'VITE_FIREBASE_API_KEY': import.meta.env.VITE_FIREBASE_API_KEY,
    'VITE_FIREBASE_PROJECT_ID': import.meta.env.VITE_FIREBASE_PROJECT_ID,
    'VITE_FIREBASE_APP_ID': import.meta.env.VITE_FIREBASE_APP_ID
  };

  const missingVars = Object.entries(requiredVars)
    .filter(([_, value]) => !value)
    .map(([key]) => key);

  if (missingVars.length > 0) {
    throw new Error(
      `Missing required Firebase configuration: ${missingVars.join(', ')}. ` +
      'Please check your environment variables.'
    );
  }
}

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: `${import.meta.env.VITE_FIREBASE_PROJECT_ID}.firebaseapp.com`,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: `${import.meta.env.VITE_FIREBASE_PROJECT_ID}.appspot.com`,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};

let auth;
let googleProvider;

try {
  if (!import.meta.env.DEV) {
    validateFirebaseConfig();
  }
  const app = initializeApp(firebaseConfig);
  auth = getAuth(app);
  googleProvider = new GoogleAuthProvider();

  // Restrict to @agile6.com domain
  googleProvider.setCustomParameters({
    hd: 'agile6.com'
  });
} catch (error) {
  console.error('Firebase initialization error:', error);
  // Re-throw the error with a more descriptive message
  throw new Error(
    `Failed to initialize Firebase: ${error.message}. ` +
    'Please check your Firebase configuration and environment variables.'
  );
}

export { auth, googleProvider };