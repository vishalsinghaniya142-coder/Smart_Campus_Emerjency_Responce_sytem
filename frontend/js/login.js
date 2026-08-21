document.addEventListener(
    "DOMContentLoaded",
    () => {

        const form =
            document.getElementById(
                "login-form"
            );

        const message =
            document.getElementById(
                "auth-message"
            );


        function showMessage(
            text,
            type = "error"
        ) {

            message.textContent = text;

            message.className =
                `auth-message ${type}`;
        }


        function loading(
            button,
            state
        ) {

            if (!button) return;

            button.disabled = state;

            if (state) {

                button.dataset.original =
                    button.innerHTML;

                button.innerHTML =
                    `<i class="fa-solid fa-circle-notch fa-spin"></i>
                     Please wait...`;

            } else {

                button.innerHTML =
                    button.dataset.original ||
                    "Continue";
            }
        }


        // EMAIL LOGIN

        form?.addEventListener(
            "submit",
            async event => {

                event.preventDefault();

                const email =
                    document.getElementById(
                        "email"
                    ).value.trim();

                const password =
                    document.getElementById(
                        "password"
                    ).value;


                const button =
                    document.getElementById(
                        "login-submit"
                    );


                try {

                    loading(button, true);

                    await Auth.loginWithEmail(
                        email,
                        password
                    );

                    showMessage(
                        "Login successful. Redirecting...",
                        "success"
                    );

                    setTimeout(
                        () => {
                            window.location.href =
                                "dashboard.html";
                        },
                        500
                    );

                } catch (error) {

                    console.error(error);

                    showMessage(
                        getFirebaseError(
                            error
                        )
                    );

                    loading(button, false);
                }
            }
        );


        // GOOGLE

        document
            .getElementById(
                "google-login"
            )
            ?.addEventListener(
                "click",
                async event => {

                    const button =
                        event.currentTarget;

                    try {

                        loading(button, true);

                        await Auth.loginWithGoogle();

                        window.location.href =
                            "dashboard.html";

                    } catch (error) {

                        showMessage(
                            getFirebaseError(
                                error
                            )
                        );

                        loading(button, false);
                    }
                }
            );


        // PHONE MODAL

        const phoneModal =
            document.getElementById(
                "phone-modal"
            );


        const phoneButton =
            document.getElementById(
                "phone-login"
            );

        if (phoneButton && !window.Auth?.firebaseEnabled) {
            phoneButton.disabled = true;
            phoneButton.title = "Use the email or phone number field above to sign in.";
            phoneButton.innerHTML = `
                <i class="fa-solid fa-mobile-screen-button"></i>
                Use email / phone login
            `;
        }

        phoneButton
            ?.addEventListener(
                "click",
                () => {

                    if (!window.Auth?.firebaseEnabled) {
                        showMessage(
                            "Phone OTP is unavailable because Firebase Auth is not configured. Please use the email or phone number field above.",
                            "error"
                        );
                        return;
                    }

                    phoneModal
                        ?.classList
                        .remove("hidden");
                }
            );


        document
            .getElementById(
                "close-phone"
            )
            ?.addEventListener(
                "click",
                () => {

                    phoneModal
                        ?.classList
                        .add("hidden");
                }
            );


        // SEND OTP

        document
            .getElementById(
                "send-otp"
            )
            ?.addEventListener(
                "click",
                async event => {

                    const button =
                        event.currentTarget;

                    const phone =
                        document
                            .getElementById(
                                "phone-input"
                            )
                            .value
                            .trim();


                    if (
                        !/^\+\d{10,15}$/.test(
                            phone
                        )
                    ) {

                        alert(
                            "Use international format, e.g. +919876543210"
                        );

                        return;
                    }


                    try {

                        loading(button, true);

                        await Auth.sendPhoneOTP(
                            phone
                        );

                        document
                            .getElementById(
                                "otp-section"
                            )
                            .classList
                            .remove("hidden");

                        button.textContent =
                            "OTP sent";

                        button.disabled =
                            true;

                    } catch (error) {

                        console.error(error);

                        alert(
                            getFirebaseError(
                                error
                            )
                        );

                        loading(
                            button,
                            false
                        );
                    }
                }
            );


        // VERIFY OTP

        document
            .getElementById(
                "verify-otp"
            )
            ?.addEventListener(
                "click",
                async event => {

                    const button =
                        event.currentTarget;

                    const code =
                        document
                            .getElementById(
                                "otp-input"
                            )
                            .value
                            .trim();


                    if (
                        !/^\d{6}$/.test(
                            code
                        )
                    ) {

                        alert(
                            "Enter the 6-digit OTP."
                        );

                        return;
                    }


                    try {

                        loading(
                            button,
                            true
                        );

                        await Auth.verifyPhoneOTP(
                            code
                        );

                        window.location.href =
                            "dashboard.html";

                    } catch (error) {

                        alert(
                            getFirebaseError(
                                error
                            )
                        );

                        loading(
                            button,
                            false
                        );
                    }
                }
            );


        // FORGOT PASSWORD

        const forgotModal =
            document.getElementById(
                "forgot-modal"
            );


        document
            .getElementById(
                "forgot-password"
            )
            ?.addEventListener(
                "click",
                () => {

                    const email =
                        document
                            .getElementById(
                                "email"
                            )
                            .value;

                    document
                        .getElementById(
                            "reset-email"
                        )
                        .value = email;

                    forgotModal
                        ?.classList
                        .remove("hidden");
                }
            );


        document
            .getElementById(
                "close-forgot"
            )
            ?.addEventListener(
                "click",
                () => {

                    forgotModal
                        ?.classList
                        .add("hidden");
                }
            );


        document
            .getElementById(
                "send-reset"
            )
            ?.addEventListener(
                "click",
                async event => {

                    const email =
                        document
                            .getElementById(
                                "reset-email"
                            )
                            .value
                            .trim();

                    if (!email) {

                        alert(
                            "Enter your email address."
                        );

                        return;
                    }


                    try {

                        loading(
                            event.currentTarget,
                            true
                        );

                        await Auth.forgotPassword(
                            email
                        );

                        alert(
                            "Password reset link sent. Check your email."
                        );

                        forgotModal
                            ?.classList
                            .add("hidden");

                    } catch (error) {

                        alert(
                            getFirebaseError(
                                error
                            )
                        );

                    } finally {

                        loading(
                            event.currentTarget,
                            false
                        );
                    }
                }
            );


        // PASSWORD VISIBILITY

        document
            .querySelectorAll(
                ".password-toggle"
            )
            .forEach(
                button => {

                    button.addEventListener(
                        "click",
                        () => {

                            const target =
                                document.getElementById(
                                    button.dataset.target
                                );

                            if (
                                target.type ===
                                "password"
                            ) {

                                target.type =
                                    "text";

                                button.innerHTML =
                                    `<i class="fa-regular fa-eye-slash"></i>`;

                            } else {

                                target.type =
                                    "password";

                                button.innerHTML =
                                    `<i class="fa-regular fa-eye"></i>`;
                            }
                        }
                    );
                }
            );

    }
);


// ======================================================
// FIREBASE ERROR FORMATTER
// ======================================================

function getFirebaseError(error) {

    const code =
        error?.code || "";

    const errors = {

        "auth/invalid-credential":
            "Email or password is incorrect.",

        "auth/invalid-email":
            "Please enter a valid email address.",

        "auth/user-not-found":
            "No account exists with this email.",

        "auth/wrong-password":
            "Incorrect password.",

        "auth/email-already-in-use":
            "An account already exists with this email.",

        "auth/weak-password":
            "Password should be at least 6 characters.",

        "auth/popup-closed-by-user":
            "Authentication window was closed.",

        "auth/popup-blocked":
            "Your browser blocked the authentication popup.",

        "auth/operation-not-allowed":
            "GitHub login is not enabled in Firebase. Enable GitHub under Firebase Console > Authentication > Sign-in method.",

        "auth/account-exists-with-different-credential":
            "This email already uses another login method. Sign in with that method first.",

        "auth/invalid-verification-code":
            "The OTP is incorrect.",

        "auth/too-many-requests":
            "Too many attempts. Please try again later."
    };


    return (
        errors[code] ||
        error?.message ||
        "Authentication failed."
    );
}


window.getFirebaseError =
    getFirebaseError;