document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("catalogFilterToggle");
    const drawer = document.getElementById("catalogFilterDrawer");
    const backdrop = document.getElementById("catalogFilterBackdrop");
    const closeButton = document.getElementById("catalogFilterClose");

    if (!toggle || !drawer || !backdrop || !closeButton) {
        return;
    }

    const form = document.getElementById("catalogSearchForm");
    const main = document.querySelector(".main");
    const topbar = document.querySelector(".topbar");
    if (form) {
        drawer.querySelectorAll("input, select, textarea, button[type='submit']").forEach((control) => {
            control.setAttribute("form", form.id);
        });
    }

    document.body.append(backdrop, drawer);

    let returnFocus = null;

    const setOverlayPosition = () => {
        const headerBottom = topbar ? Math.max(0, topbar.getBoundingClientRect().bottom) : 0;
        const contentLeft = main ? Math.max(0, main.getBoundingClientRect().left) : 0;
        document.documentElement.style.setProperty(
            "--catalog-header-bottom",
            `${headerBottom}px`
        );
        document.documentElement.style.setProperty(
            "--catalog-content-left",
            `${contentLeft}px`
        );
    };

    const scheduleOverlayPosition = () => {
        window.requestAnimationFrame(() => {
            if (drawer.classList.contains("is-open")) {
                setOverlayPosition();
            }
        });
    };

    const closeDrawer = () => {
        drawer.classList.remove("is-open");
        backdrop.classList.remove("is-open");
        drawer.setAttribute("aria-hidden", "true");
        toggle.setAttribute("aria-expanded", "false");
        document.body.classList.remove("catalog-filter-open");
        if (returnFocus) {
            returnFocus.focus();
            returnFocus = null;
        }
    };

    const openDrawer = () => {
        setOverlayPosition();
        returnFocus = document.activeElement;
        drawer.classList.add("is-open");
        backdrop.classList.add("is-open");
        drawer.setAttribute("aria-hidden", "false");
        toggle.setAttribute("aria-expanded", "true");
        document.body.classList.add("catalog-filter-open");
        closeButton.focus();
    };

    toggle.addEventListener("click", openDrawer);
    closeButton.addEventListener("click", closeDrawer);
    backdrop.addEventListener("click", closeDrawer);
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && drawer.classList.contains("is-open")) {
            closeDrawer();
            return;
        }
        if (event.key === "Tab" && drawer.classList.contains("is-open")) {
            const focusable = drawer.querySelectorAll(
                'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), summary'
            );
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }
    });
    window.addEventListener("resize", () => {
        scheduleOverlayPosition();
    });

    if (drawer.querySelector(".catalog-search-error-list")) {
        openDrawer();
    }
});
