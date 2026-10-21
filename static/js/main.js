document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
  }
  document.querySelectorAll(".flash").forEach((item) => {
    window.setTimeout(() => {
      item.style.transition = "opacity .4s ease";
      item.style.opacity = "0";
      window.setTimeout(() => item.remove(), 450);
    }, 5000);
  });
});