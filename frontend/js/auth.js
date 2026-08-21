import {
    initializeApp
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";

import {
    getAuth,
    GoogleAuthProvider,
    RecaptchaVerifier,
    signInWithPopup,
    signInWithPhoneNumber,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    updateProfile,
    sendPasswordResetEmail,
    signOut,
    onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";


// ======================================================
// FIREBASE CONFIG
// ======================================================
//
// Firebase Console:
// Project Settings
// → Your Apps
// → Web App
// → Firebase SDK configuration
//
// IMPORTANT:
// Replace the placeholder values below.
// ======================================================

const firebaseConfig = {
    apiKey: "AIzaSyDrVpC3bOzwX6U5BiZ2nzQJISyuuWOqfak",
    authDomain: "smart-campus-ai-emergency.firebaseapp.com",
    projectId: "smart-campus-ai-emergency",
    storageBucket: "smart-campus-ai-emergency.firebasestorage.app",
    messagingSenderId: "682147663086",
    appId: "1:682147663086:web:8a0e651d3547725cebb7ff",
    measurementId: "G-ZFNDHKVRH6"
};


// ======================================================
// INITIALIZE FIREBASE
// ======================================================

let auth = null;
let firebaseEnabled = false;

function ensureSupportReference() {
    let reference = localStorage.getItem("support_reference");
    if (!reference) {
        const suffix = typeof crypto !== "undefined" && crypto.randomUUID
            ? crypto.randomUUID().split("-")[0].toUpperCase()
            : Math.random().toString(36).slice(2, 8).toUpperCase();
        reference = `SS-${suffix}`;
        localStorage.setItem("support_reference", reference);
    }
    return reference;
}

const hasFirebaseWebConfig = Boolean(
    firebaseConfig.apiKey &&
    firebaseConfig.authDomain &&
    firebaseConfig.projectId &&
    firebaseConfig.appId
);

if (hasFirebaseWebConfig) {
    try {
        const firebaseApp = initializeApp(firebaseConfig);
        auth = getAuth(firebaseApp);
        firebaseEnabled = true;
    } catch (error) {
        console.warn("Firebase initialization failed; backend email auth remains active.", error);
        auth = null;
        firebaseEnabled = false;
    }
} else {
    console.warn("Firebase web configuration is missing; using backend email auth only.");
    auth = null;
    firebaseEnabled = false;
}

function requireFirebaseAuth() {
    if (!auth || !firebaseEnabled) {
        throw new Error(
            "Firebase Auth is not configured for this app. Please use email login or configure Firebase web SDK settings in the project."
        );
    }

    return auth;
}


// ======================================================
// PROVIDERS
// ======================================================

const googleProvider =
    new GoogleAuthProvider();

googleProvider.setCustomParameters({
    prompt: "select_account"
});


// ======================================================
// BACKEND TOKEN EXCHANGE
// ======================================================
//
// Firebase authenticates the user.
// FastAPI creates its own JWT.
//
// Firebase ID Token
//       ↓
// POST /auth/firebase
//       ↓
// FastAPI JWT
//       ↓
// Protected APIs
// ======================================================

async function exchangeToken(user) {

    const firebaseToken =
        await user.getIdToken(true);

    const response =
        await API.post(
            "/auth/firebase",
            {
                id_token: firebaseToken
            }
        );

    const data =
        response.data || response;

    if (!data.access_token) {

        throw new Error(
            "Backend authentication token was not generated."
        );
    }

    localStorage.setItem(
        "emergency_token",
        data.access_token
    );

    localStorage.setItem(
        "profileName",
        user.displayName ||
        user.phoneNumber ||
        user.email?.split("@")[0] ||
        "Campus User"
    );

    localStorage.setItem(
        "profileEmail",
        user.email || ""
    );

    localStorage.setItem(
        "profilePhoto",
        user.photoURL || ""
    );

    localStorage.setItem(
        "profileProvider",
        user.providerData?.[0]?.providerId || "firebase"
    );
    ensureSupportReference();

    return data;
}


// ======================================================
// EMAIL LOGIN (Backend-based)
// ======================================================

async function loginWithEmail(
    emailOrPhone,
    password
) {

    const identifier =
        String(emailOrPhone || "").trim();

    if (!identifier) {
        throw new Error("Please enter your email or phone number.");
    }

    const payload = identifier.includes("@")
        ? { email: identifier, password }
        : { phone_number: identifier, password };

    const response =
        await API.post(
            "/auth/login",
            payload
        );

    const data =
        response.data || response;

    if (!data.access_token) {

        throw new Error(
            "Backend authentication token was not generated."
        );
    }

    localStorage.setItem(
        "emergency_token",
        data.access_token
    );

    if (data.user) {

        localStorage.setItem(
            "profileName",
            data.user.name ||
            identifier.split("@")[0] ||
            "Campus User"
        );

        localStorage.setItem(
            "profileEmail",
            data.user.email || (identifier.includes("@") ? identifier : "")
        );

        localStorage.setItem(
            "profileProvider",
            "email"
        );
        ensureSupportReference();
    }

    return data;
}


// ======================================================
// EMAIL REGISTER
// ======================================================

async function registerWithEmail(
    name,
    email,
    password
) {

    if (!firebaseEnabled) {
        const response = await API.post(
            "/auth/register",
            {
                name,
                email,
                password,
                phone_number: "",
                role: "student"
            }
        );

        const data = response.data || response;
        const user = data.user || data;

        if (!user) {
            throw new Error("User registration failed on the backend.");
        }

        const login = await loginWithEmail(email, password);
        return login.user || user;
    }

    const firebaseAuth = requireFirebaseAuth();

    const credential =
        await createUserWithEmailAndPassword(
            firebaseAuth,
            email,
            password
        );

    await updateProfile(
        credential.user,
        {
            displayName: name
        }
    );

    await exchangeToken(
        credential.user
    );

    return credential.user;
}


// ======================================================
// GOOGLE LOGIN
// ======================================================

async function loginWithGoogle() {

    if (!firebaseEnabled) {
        throw new Error("Google sign-in is unavailable because Firebase Auth is not configured.");
    }

    const firebaseAuth = requireFirebaseAuth();

    const result =
        await signInWithPopup(
            firebaseAuth,
            googleProvider
        );

    await exchangeToken(
        result.user
    );

    return result.user;
}


// ======================================================
// PHONE OTP
// ======================================================

function createRecaptcha() {

    if (!firebaseEnabled) {
        throw new Error("Phone OTP is unavailable because Firebase Auth is not configured.");
    }

    const firebaseAuth = requireFirebaseAuth();

    if (
        window.recaptchaVerifier
    ) {
        return window.recaptchaVerifier;
    }

    window.recaptchaVerifier =
        new RecaptchaVerifier(
            firebaseAuth,
            "recaptcha-container",
            {
                size: "invisible",

                callback: () => {
                    console.log(
                        "reCAPTCHA verified."
                    );
                },

                "expired-callback": () => {

                    window.recaptchaVerifier =
                        null;
                }
            }
        );

    return window.recaptchaVerifier;
}


async function sendPhoneOTP(
    phoneNumber
) {

    const firebaseAuth = requireFirebaseAuth();

    const verifier =
        createRecaptcha();

    const confirmation =
        await signInWithPhoneNumber(
            firebaseAuth,
            phoneNumber,
            verifier
        );

    window.phoneConfirmation =
        confirmation;

    return true;
}


async function verifyPhoneOTP(
    code
) {

    if (
        !window.phoneConfirmation
    ) {

        throw new Error(
            "Please request an OTP first."
        );
    }

    const result =
        await window.phoneConfirmation.confirm(
            code
        );

    await exchangeToken(
        result.user
    );

    return result.user;
}


// ======================================================
// FORGOT PASSWORD
// ======================================================

async function forgotPassword(
    email
) {

    const firebaseAuth = requireFirebaseAuth();

    await sendPasswordResetEmail(
        firebaseAuth,
        email
    );

    return true;
}


// ======================================================
// LOGOUT
// ======================================================

async function logout() {

    if (auth) {
        await signOut(auth);
    }

    API.clearSession();

    window.location.href =
        "index.html";
}


// ======================================================
// AUTH STATE
// ======================================================

if (auth) {
    onAuthStateChanged(
        auth,
        user => {
            window.currentFirebaseUser = user || null;
        }
    );
}


// ======================================================
// GLOBAL AUTH OBJECT
// ======================================================

window.Auth = {

    auth,

    firebaseEnabled,

    isFirebasePhoneLoginAvailable: Boolean(auth && firebaseEnabled),

    loginWithEmail,

    registerWithEmail,

    loginWithGoogle,


    sendPhoneOTP,

    verifyPhoneOTP,

    forgotPassword,

    logout,

    exchangeToken
};