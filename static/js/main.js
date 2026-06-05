// QoS Ticketing - Main JavaScript

// Subcategory dynamic loading on ticket forms
function initSubcategoryLoader() {
  const catSelect = document.getElementById('id_category');
  const subSelect = document.getElementById('id_sub_category');
  if (!catSelect || !subSelect) return;

  catSelect.addEventListener('change', function () {
    const catId = this.value;
    if (!catId) {
      subSelect.innerHTML = '<option value="">---------</option>';
      return;
    }
    fetch(`/tickets/api/subcategories/?category_id=${catId}`)
      .then(r => r.json())
      .then(data => {
        subSelect.innerHTML = '<option value="">---------</option>';
        data.subcategories.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.id;
          opt.textContent = s.name;
          subSelect.appendChild(opt);
        });
      })
      .catch(() => {});
  });
}

// Confirm destructive actions
function initConfirmButtons() {
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
  });
}

// Auto-dismiss alerts after 5s
function initAlertDismiss() {
  setTimeout(() => {
    document.querySelectorAll('.alert.auto-dismiss').forEach(el => {
      const alert = bootstrap.Alert.getOrCreateInstance(el);
      if (alert) alert.close();
    });
  }, 5000);
}

// Sidebar responsive toggle for mobile
function initMobileSidebar() {
  const toggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  if (!toggle || !sidebar) return;
  // On mobile, toggle 'show' class
  if (window.innerWidth < 768) {
    toggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    document.addEventListener('click', e => {
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    });
  }
}

// Mark notification as read on click
function initNotificationLinks() {
  document.querySelectorAll('.notif-item[href]').forEach(link => {
    link.addEventListener('click', function () {
      const pk = this.dataset.pk;
      if (pk) {
        fetch(`/notifications/${pk}/read/`, { method: 'POST', headers: { 'X-CSRFToken': getCsrfToken() } });
      }
    });
  });
}

function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initSubcategoryLoader();
  initConfirmButtons();
  initAlertDismiss();
  initMobileSidebar();
  initNotificationLinks();
});
