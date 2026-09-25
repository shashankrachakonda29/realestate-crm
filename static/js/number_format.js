document.addEventListener("DOMContentLoaded", function () {

    function formatIndianNumber(value) {

        value = String(value)
            .replace(/₹/g, "")
            .replace(/,/g, "")
            .trim();

        if (value === "" || value === "—" || isNaN(value)) {
            return value;
        }

        const parts = value.split(".");
        let number = parts[0];
        const decimal = parts[1];

        let lastThree = number.slice(-3);
        let remaining = number.slice(0, -3);

        if (remaining) {
            remaining = remaining.replace(
                /\B(?=(\d{2})+(?!\d))/g,
                ","
            );

            number = remaining + "," + lastThree;
        }

        return decimal !== undefined
            ? number + "." + decimal
            : number;
    }


    function isFormField(element) {
        return (
            element.tagName === "INPUT" ||
            element.tagName === "TEXTAREA" ||
            element.tagName === "SELECT"
        );
    }


    function formatElement(element) {

        if (isFormField(element)) {

            // For form fields, keep only the numeric value
            element.value = formatIndianNumber(
                element.value
            );

        } else {

            const originalText = element.textContent.trim();

            // Check whether ₹ already exists
            const hasRupee = originalText.includes("₹");

            const formattedValue = formatIndianNumber(
                originalText
            );

            if (
                formattedValue === "" ||
                formattedValue === "—"
            ) {
                element.textContent = formattedValue;
            } else if (hasRupee) {
                element.textContent = "₹ " + formattedValue;
            } else {
                element.textContent = formattedValue;
            }

        }
    }


    // Format all existing elements
    function formatAll() {

        document
            .querySelectorAll(".comma-format")
            .forEach(function (element) {

                formatElement(element);

            });

    }


    // Input fields
    document.addEventListener("input", function (event) {

        if (
            event.target.classList &&
            event.target.classList.contains("comma-format")
        ) {

            formatElement(event.target);

        }

    });


    // Change event
    document.addEventListener("change", function (event) {

        if (
            event.target.classList &&
            event.target.classList.contains("comma-format")
        ) {

            formatElement(event.target);

        }

    });


    // Remove commas and ₹ before submitting forms
    document.querySelectorAll("form").forEach(function (form) {

        form.addEventListener("submit", function () {

            form
                .querySelectorAll(".comma-format")
                .forEach(function (element) {

                    if (isFormField(element)) {

                        element.value = element.value
                            .replace(/₹/g, "")
                            .replace(/,/g, "")
                            .trim();

                    }

                });

        });

    });


    // Initial formatting
    formatAll();

});