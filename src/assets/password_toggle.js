document.addEventListener("DOMContentLoaded", function () {
  function togglePassword(targetId, iconEl) {
    if (!targetId) return;
    const input = document.getElementById(targetId);
    if (!input) return;
    const icon =
      iconEl || (iconEl.nodeName === "I" ? iconEl : iconEl.querySelector("i"));
    if (input.type === "password") {
      input.type = "text";
      if (icon) {
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      }
    } else {
      input.type = "password";
      if (icon) {
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    }
  }

  document.body.addEventListener("click", function (e) {
    const toggle = e.target.closest(".pw-toggle");
    if (!toggle) return;
    const target = toggle.dataset && toggle.dataset.target;
    const icon = toggle.querySelector("i") || toggle;
    togglePassword(target, icon);
  });
});
