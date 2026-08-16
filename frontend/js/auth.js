import {
    initializeApp
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";

import {
    getAuth,
    GoogleAuthProvider,
    GithubAuthProvider,
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

    apiKey: "PASTE_YOUR_FIREBASE_API_KEY",

    authDomain:
        "smart-campus-ai-emergency.firebaseapp.com",

    projectId:
        "smart-campus-ai-emergency",

    storageBucket:
        "PASTE_YOUR_STORAGE_BUCKET",

    messagingSenderId:
        "PASTE_YOUR_MESSAGING_SENDER_ID",

    appId:
        "PASTE_YOUR_FIREBASE_APP_ID"
};


// ======================================================
// INITIALIZE FIREBASE
// ======================================================

const firebaseApp =
    initializeApp(firebaseConfig);

const auth =
    getAuth(firebaseApp);


// ======================================================
// PROVIDERS
// ======================================================

const googleProvider =
    new GoogleAuthProvider();

googleProvider.setCustomParameters({
    prompt: "select_account"
});


const githubProvider =
    new GithubAuthProvider();


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

    return data;
}


// ======================================================
// EMAIL LOGIN
// ======================================================

async function loginWithEmail(
    email,
    password
) {

    const credential =
        await signInWithEmailAndPassword(
            auth,
            email,
            password
        );

    await exchangeToken(
        credential.user
    );

    return credential.user;
}


// ======================================================
// EMAIL REGISTER
// ======================================================

async function registerWithEmail(
    name,
    email,
    password
) {

    const credential =
        await createUserWithEmailAndPassword(
            auth,
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

    const result =
        await signInWithPopup(
            auth,
            googleProvider
        );

    await exchangeToken(
        result.user
    );

    return result.user;
}


// ======================================================
// GITHUB LOGIN
// ======================================================

async function loginWithGithub() {

    const result =
        await signInWithPopup(
            auth,
            githubProvider
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

    if (
        window.recaptchaVerifier
    ) {
        return window.recaptchaVerifier;
    }

    window.recaptchaVerifier =
        new RecaptchaVerifier(
            auth,
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

    const verifier =
        createRecaptcha();

    const confirmation =
        await signInWithPhoneNumber(
            auth,
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

    await sendPasswordResetEmail(
        auth,
        email
    );

    return true;
}


// ======================================================
// LOGOUT
// ======================================================

async function logout() {

    await signOut(auth);

    API.clearSession();

    window.location.href =
        "index.html";
}


// ======================================================
// AUTH STATE
// ======================================================

onAuthStateChanged(
    auth,
    user => {

        window.currentFirebaseUser =
            user || null;
    }
);


// ======================================================
// GLOBAL AUTH OBJECT
// ======================================================

window.Auth = {

    auth,

    loginWithEmail,

    registerWithEmail,

    loginWithGoogle,

    loginWithGithub,

    sendPhoneOTP,

    verifyPhoneOTP,

    forgotPassword,

    logout,

    exchangeToken
};