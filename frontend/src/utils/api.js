export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// =========================================================================
// PHASE 16 — JWT AUTHENTICATION STATE & TOKEN MANAGEMENT
// =========================================================================

/**
 * Access Token is kept in application memory for defense-in-depth against XSS.
 * Refresh Token and minimal user profile are kept in localStorage for session persistence across refreshes.
 *
 * Security Trade-off Documentation:
 * Storing the rotating refresh token in localStorage allows user persistence across page reloads.
 * The refresh token is single-use/rotating and revocable server-side.
 */
let inMemoryAccessToken = null;
let isRefreshing = false;
let refreshSubscribers = [];

function subscribeTokenRefresh(cb) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

export function getAccessToken() {
  return inMemoryAccessToken;
}

export function setAuthSession({ access_token, refresh_token, user }) {
  inMemoryAccessToken = access_token;
  if (refresh_token) {
    localStorage.setItem('pathwise_refresh_token', refresh_token);
  }
  if (user) {
    localStorage.setItem('pathwise_user', JSON.stringify(user));
  }
}

export function clearAuthSession() {
  inMemoryAccessToken = null;
  localStorage.removeItem('pathwise_refresh_token');
  localStorage.removeItem('pathwise_user');
}

export function getStoredUser() {
  try {
    const raw = localStorage.getItem('pathwise_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getStoredRefreshToken() {
  return localStorage.getItem('pathwise_refresh_token');
}

export function isAuthenticated() {
  return Boolean(inMemoryAccessToken || getStoredRefreshToken());
}

/**
 * Custom fetch wrapper with automatic JWT Bearer header attachment and
 * single-attempt 401 token refresh retry.
 */
async function fetchJson(url, options = {}, isRetry = false) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  // If options.body is FormData, remove Content-Type to allow browser boundary setup
  if (options.body instanceof FormData) {
    delete headers['Content-Type'];
  }

  // Attach Bearer Access Token if present
  if (inMemoryAccessToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${inMemoryAccessToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized with automatic refresh token rotation
  if (response.status === 401 && !isRetry && !url.includes('/api/auth/login') && !url.includes('/api/auth/refresh')) {
    const refreshToken = getStoredRefreshToken();
    if (refreshToken) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshRes = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const data = await refreshRes.json();
            setAuthSession(data);
            isRefreshing = false;
            onRefreshed(data.access_token);
            // Retry original request
            return await fetchJson(url, options, true);
          } else {
            clearAuthSession();
            isRefreshing = false;
            onRefreshed(null);
            if (window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }
        } catch {
          clearAuthSession();
          isRefreshing = false;
          onRefreshed(null);
          if (window.location.pathname !== '/login') {
            window.location.href = '/login';
          }
        }
      } else {
        // Wait for active refresh to finish
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((token) => {
            if (token) {
              resolve(fetchJson(url, options, true));
            } else {
              reject(new Error('Session expired. Please log in again.'));
            }
          });
        });
      }
    }
  }

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {}
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  if (response.status === 204) {
    return null;
  }

  return await response.json();
}

/**
 * Health check endpoint.
 */
export async function checkHealth() {
  return await fetchJson('/health');
}

/**
 * =========================================================================
 * PHASE 16 — AUTHENTICATION ENDPOINTS
 * =========================================================================
 */

/**
 * Authenticates user with username and password.
 */
export async function login(username, password) {
  const data = await fetchJson('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setAuthSession(data);
  return data;
}

/**
 * Rotates the refresh token and updates access token.
 */
export async function refreshAuthToken() {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token found.');
  }
  const data = await fetchJson('/api/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  setAuthSession(data);
  return data;
}

/**
 * Logs out and revokes the active refresh token.
 */
export async function logout() {
  const refreshToken = getStoredRefreshToken();
  if (refreshToken) {
    try {
      await fetchJson('/api/auth/logout', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {}
  }
  clearAuthSession();
}

/**
 * Retrieves profile of currently authenticated user.
 */
export async function getCurrentUserProfile() {
  return await fetchJson('/api/auth/me');
}

/**
 * Live setup validation: checks username syntax and availability.
 */
export async function checkUsernameAvailability(username) {
  return await fetchJson(`/api/auth/check-username?username=${encodeURIComponent(username)}`);
}

/**
 * ADMIN only: Creates a new user account.
 */
export async function createUserAccount(payload) {
  return await fetchJson('/api/auth/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * =========================================================================
 * DASHBOARD & ACADEMICS ENDPOINTS
 * =========================================================================
 */

export async function getDashboardOverview() {
  return await fetchJson('/api/dashboard/overview');
}

export async function getDepartmentAnalytics() {
  return await fetchJson('/api/dashboard/departments');
}

export async function getStudents({
  page = 1,
  pageSize = 20,
  search = '',
  riskTier = '',
  trend = '',
  department = '',
  semester = '',
  sortBy = 'computed_at',
  sortOrder = 'desc',
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (search) params.append('search', search);
  if (riskTier) params.append('risk_tier', riskTier);
  if (trend) params.append('trend', trend);
  if (department) params.append('department', department);
  if (semester) params.append('semester', semester);
  if (sortBy) params.append('sort_by', sortBy);
  if (sortOrder) params.append('sort_order', sortOrder);

  return await fetchJson(`/api/students?${params.toString()}`);
}

export async function getStudentProfile(studentId) {
  return await fetchJson(`/api/students/${studentId}`);
}

export async function getStudentAssessment(studentId) {
  return await fetchJson(`/api/students/${studentId}/assessment`);
}

export async function computeAndPersistAssessment(studentId) {
  return await fetchJson(`/api/students/${studentId}/assessment`, {
    method: 'POST',
  });
}

export async function getRulesConfig() {
  return await fetchJson('/api/rules');
}

export async function updateRulesConfig(config) {
  return await fetchJson('/api/rules', {
    method: 'PUT',
    body: JSON.stringify(config),
  });
}

export async function uploadDataset(dataType, file) {
  const formData = new FormData();
  formData.append('file', file);

  return await fetchJson(`/api/uploads/${dataType}`, {
    method: 'POST',
    body: formData,
  });
}

/**
 * =========================================================================
 * NOTIFICATIONS ENDPOINTS
 * =========================================================================
 */

export async function getNotifications({
  page = 1,
  pageSize = 20,
  unreadOnly = false,
  severity = '',
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (unreadOnly) params.append('unread_only', 'true');
  if (severity) params.append('severity', severity);

  return await fetchJson(`/api/notifications?${params.toString()}`);
}

export async function getUnreadNotificationCount() {
  return await fetchJson('/api/notifications/unread-count');
}

export async function markNotificationAsRead(notificationId) {
  return await fetchJson(`/api/notifications/${notificationId}/read`, {
    method: 'PATCH',
  });
}

export async function markAllNotificationsAsRead() {
  return await fetchJson('/api/notifications/read-all', {
    method: 'PATCH',
  });
}

/**
 * =========================================================================
 * INTERVENTIONS ENDPOINTS
 * =========================================================================
 */

export async function createIntervention(payload) {
  return await fetchJson('/api/interventions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getInterventions({
  page = 1,
  pageSize = 20,
  studentId = null,
  mentorId = null,
  status = '',
  interventionType = '',
  followUpsDue = false,
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (studentId) params.append('student_id', studentId);
  if (mentorId) params.append('mentor_id', mentorId);
  if (status) params.append('status', status);
  if (interventionType) params.append('intervention_type', interventionType);
  if (followUpsDue) params.append('follow_ups_due', 'true');

  return await fetchJson(`/api/interventions?${params.toString()}`);
}

export async function getInterventionById(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}`);
}

export async function updateIntervention(interventionId, payload) {
  return await fetchJson(`/api/interventions/${interventionId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function deleteIntervention(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}`, {
    method: 'DELETE',
  });
}

export async function getInterventionsSummary() {
  return await fetchJson('/api/interventions/summary');
}

export async function getInterventionEffectiveness(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}/effectiveness`);
}

export async function getEffectivenessSummary() {
  return await fetchJson('/api/interventions/effectiveness/summary');
}

export async function getFollowUps({
  page = 1,
  pageSize = 20,
  state = '',
  studentId = null,
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (state) params.append('state', state);
  if (studentId) params.append('student_id', studentId);

  return await fetchJson(`/api/interventions/follow-ups?${params.toString()}`);
}
