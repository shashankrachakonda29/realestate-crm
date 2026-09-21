function toggleSidebar() {
	const sidebar = document.getElementById("sidebar");
	const overlay = document.getElementById("sidebarOverlay");

	if (!sidebar || !overlay) {
		return;
	}

	sidebar.classList.toggle("mobile-open");
	overlay.classList.toggle("active");
}

document.addEventListener("DOMContentLoaded", () => {
	const sidebar = document.getElementById("sidebar");
	const overlay = document.getElementById("sidebarOverlay");

	document.querySelectorAll(".nav-item[href]").forEach((item) => {
		item.addEventListener("click", () => {
			if (window.innerWidth <= 700 && sidebar && overlay) {
				sidebar.classList.remove("mobile-open");
				overlay.classList.remove("active");
			}
		});
	});

	window.addEventListener("resize", () => {
		if (window.innerWidth > 700 && sidebar && overlay) {
			sidebar.classList.remove("mobile-open");
			overlay.classList.remove("active");
		}
	});
});