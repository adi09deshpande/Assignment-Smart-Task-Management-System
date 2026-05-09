/* Shared JS utilities. */

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'info'} type
 * @param {number} duration ms before auto-dismiss
 */
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const icons = { success: 'OK', error: 'X', info: 'i' };
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `<span class="toast__icon">${icons[type] ?? 'i'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('removing');
    toast.addEventListener('animationend', () => toast.remove());
  }, duration);
}

function setFieldError(field, messageEl, message) {
  if (!field || !messageEl) return;

  if (message) {
    field.classList.add('field__input--error');
    messageEl.textContent = message;
    messageEl.classList.remove('hidden');
  } else {
    field.classList.remove('field__input--error');
    messageEl.textContent = '';
    messageEl.classList.add('hidden');
  }
}

function initRegisterForm() {
  const form = document.querySelector('[data-register-form]');
  if (!form) return;

  const password = document.getElementById('password');
  const confirmPassword = document.getElementById('confirm_password');
  const passwordError = document.getElementById('passwordError');
  const confirmPasswordError = document.getElementById('confirmPasswordError');

  function getPasswordError(value) {
    if (!value) return '';
    if (value.length < 8) return 'Password must be at least 8 characters.';
    if (!/[A-Z]/.test(value)) return 'Password must contain at least one uppercase letter.';
    if (!/[0-9]/.test(value)) return 'Password must contain at least one number.';
    return '';
  }

  function validatePasswordField() {
    const error = getPasswordError(password.value);
    setFieldError(password, passwordError, error);
    password.setCustomValidity(error);
    return !error;
  }

  function validateConfirmPasswordField() {
    let error = '';
    if (confirmPassword.value && confirmPassword.value !== password.value) {
      error = 'Passwords do not match.';
    }
    setFieldError(confirmPassword, confirmPasswordError, error);
    confirmPassword.setCustomValidity(error);
    return !error;
  }

  password.addEventListener('input', () => {
    validatePasswordField();
    validateConfirmPasswordField();
  });

  confirmPassword.addEventListener('input', validateConfirmPasswordField);

  form.addEventListener('submit', e => {
    const passwordValid = validatePasswordField();
    const confirmValid = validateConfirmPasswordField();

    if (!passwordValid || !confirmValid) {
      e.preventDefault();
    }
  });
}

function initLoginForm() {
  const form = document.querySelector('[data-login-form]');
  if (!form) return;

  const identifier = document.getElementById('identifier');
  const password = document.getElementById('password');
  const identifierError = document.getElementById('identifierError');
  const passwordError = document.getElementById('loginPasswordError');

  function validateIdentifierField() {
    const value = identifier.value.trim();
    const error = value ? '' : 'Username or email is required.';
    setFieldError(identifier, identifierError, error);
    identifier.setCustomValidity(error);
    return !error;
  }

  function validatePasswordField() {
    const error = password.value ? '' : 'Password is required.';
    setFieldError(password, passwordError, error);
    password.setCustomValidity(error);
    return !error;
  }

  identifier.addEventListener('input', validateIdentifierField);
  password.addEventListener('input', validatePasswordField);

  form.addEventListener('submit', e => {
    const identifierValid = validateIdentifierField();
    const passwordValid = validatePasswordField();

    if (!identifierValid || !passwordValid) {
      e.preventDefault();
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initRegisterForm();
  initLoginForm();
});
