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

  // Log config presence without exposing values
  console.log('Firebase config validation:', {
    apiKey: !!import.meta.env.VITE_FIREBASE_API_KEY,
    projectId: !!import.meta.env.VITE_FIREBASE_PROJECT_ID,
    appId: !!import.meta.env.VITE_FIREBASE_APP_ID
  });
}

let auth;
let googleProvider;

try {
  // Skip Firebase initialization in development
  if (import.meta.env.DEV) {
    console.log('Development mode: Skipping Firebase initialization');
    auth = null;
    googleProvider = null;
  } else {
    // Validate config before creating firebaseConfig object
    validateFirebaseConfig();

    const firebaseConfig = {
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
      authDomain: `${import.meta.env.VITE_FIREBASE_PROJECT_ID}.firebaseapp.com`,
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
      storageBucket: `${import.meta.env.VITE_FIREBASE_PROJECT_ID}.appspot.com`,
      messagingSenderId: "376645885554",
      appId: import.meta.env.VITE_FIREBASE_APP_ID,
    };

    console.log('Initializing Firebase with config structure:', {
      hasApiKey: !!firebaseConfig.apiKey,
      hasAuthDomain: !!firebaseConfig.authDomain,
      hasProjectId: !!firebaseConfig.projectId,
      hasStorageBucket: !!firebaseConfig.storageBucket,
      hasMessagingSenderId: !!firebaseConfig.messagingSenderId,
      hasAppId: !!firebaseConfig.appId,
      authDomain: firebaseConfig.authDomain // Log the actual domain for verification
    });

    const app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();

    // Restrict to @agile6.com domain
    googleProvider.setCustomParameters({
      hd: 'agile6.com'
    });

    console.log('Firebase initialized successfully');
  }
} catch (error: any) {
  console.error('Firebase initialization error:', error);
  const errorMessage = error.code === 'auth/configuration-not-found'
    ? 'Firebase project is not configured for web authentication. Please ensure:\n' +
      '1. Your domain is added to authorized domains in Firebase Console\n' +
      '2. Web application is properly configured in the Firebase project\n' +
      '3. OAuth consent screen is set up in the Google Cloud Console\n' +
      '4. Firebase Hosting is linked to your app (shown in Firebase Console setup)'
    : `Failed to initialize Firebase: ${error.message}. Please check your Firebase configuration and environment variables.`;

  throw new Error(errorMessage);
}

export { auth, googleProvider };