document.addEventListener(
    "DOMContentLoaded",
    () => {

        const form =
            document.getElementById(
                "register-form"
            );

        const message =
            document.getElementById(
                "auth-message"
            );


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
                     Creating account...`;

            } else {

                button.innerHTML =
                    button.dataset.original ||
                    "Create account";
            }
        }


        function showMessage(
            text,
            type = "error"
        ) {

            message.textContent = text;

            message.className =
                `auth-message ${type}`;
        }


        // EMAIL REGISTER

        form?.addEventListener(
            "submit",
            async event => {

                event.preventDefault();

                const name =
                    document.getElementById(
                        "name"
                    ).value.trim();

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
                        "register-submit"
                    );


                if (
                    password.length < 8
                ) {

                    showMessage(
                        "Password must contain at least 8 characters."
                    );

                    return;
                }


                try {

                    loading(
                        button,
                        true
                    );

                    await Auth.registerWithEmail(
                        name,
                        email,
                        password
                    );

                    showMessage(
                        "Account created successfully!",
                        "success"
                    );

                    setTimeout(
                        () => {

                            window.location.href =
                                "dashboard.html";

                        },
                        700
                    );

                } catch (error) {

                    console.error(error);

                    showMessage(
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


        // GOOGLE

        document
            .getElementById(
                "google-register"
            )
            ?.addEventListener(
                "click",
                async event => {

                    try {

                        loading(
                            event.currentTarget,
                            true
                        );

                        await Auth.loginWithGoogle();

                        window.location.href =
                            "dashboard.html";

                    } catch (error) {

                        showMessage(
                            getFirebaseError(
                                error
                            )
                        );

                        loading(
                            event.currentTarget,
                            false
                        );
                    }
                }
            );


        // GITHUB

        document
            .getElementById(
                "github-register"
            )
            ?.addEventListener(
                "click",
                async event => {

                    try {

                        loading(
                            event.currentTarget,
                            true
                        );

                        await Auth.loginWithGithub();

                        window.location.href =
                            "dashboard.html";

                    } catch (error) {

                        showMessage(
                            getFirebaseError(
                                error
                            )
                        );

                        loading(
                            event.currentTarget,
                            false
                        );
                    }
                }
            );


        // PHONE

        const modal =
            document.getElementById(
                "phone-modal"
            );


        document
            .getElementById(
                "phone-register"
            )
            ?.addEventListener(
                "click",
                () => {

                    modal
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

                    modal
                        ?.classList
                        .add("hidden");
                }
            );


        document
            .getElementById(
                "send-otp"
            )
            ?.addEventListener(
                "click",
                async event => {

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

                        await Auth.sendPhoneOTP(
                            phone
                        );

                        document
                            .getElementById(
                                "otp-section"
                            )
                            .classList
                            .remove("hidden");

                        event.currentTarget.disabled =
                            true;

                        event.currentTarget.textContent =
                            "OTP sent";

                    } catch (error) {

                        alert(
                            getFirebaseError(
                                error
                            )
                        );
                    }
                }
            );


        document
            .getElementById(
                "verify-otp"
            )
            ?.addEventListener(
                "click",
                async event => {

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

                            const input =
                                document.getElementById(
                                    button.dataset.target
                                );

                            if (
                                input.type ===
                                "password"
                            ) {

                                input.type =
                                    "text";

                                button.innerHTML =
                                    `<i class="fa-regular fa-eye-slash"></i>`;

                            } else {

                                input.type =
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