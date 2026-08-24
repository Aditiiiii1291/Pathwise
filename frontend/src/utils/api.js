export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Generic API request wrapper with standardized JSON response and error handling.
 */
async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, options);

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

    return await response.json();
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const connError = new Error('Backend connection refused. Ensure the Pathwise FastAPI server is running.');
      connError.status = 503;
      throw connError;
    }
    throw err;
  }
}

/**
 * Health check endpoint.
 */
export async function checkHealth() {
  return await fetchJson('/health');
}

/**
 * High-level dashboard aggregate metrics and distributions.
 */
export async function getDashboardOverview() {
  return await fetchJson('/api/dashboard/overview');
}

/**
 * Department-level risk metrics and distribution.
 */
export async function getDepartmentAnalytics() {
  return await fetchJson('/api/dashboard/departments');
}

/**
 * Paginated student directory with search and multi-attribute filters.
 */
export async function getStudents({
  page = 1,
  pageSize = 20,
  search = '',
  department = '',
  semester = '',
  riskTier = '',
  trend = '',
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (search) params.append('search', search);
  if (department) params.append('department', department);
  if (semester) params.append('semester', semester);
  if (riskTier) params.append('risk_tier', riskTier);
  if (trend) params.append('trend', trend);

  return await fetchJson(`/api/students?${params.toString()}`);
}

/**
 * Complete student profile dossier by student ID.
 */
export async function getStudentProfile(studentId) {
  return await fetchJson(`/api/students/${studentId}`);
}

/**
 * Student risk assessment & explanation (Read-Only on-demand calculation).
 */
export async function getStudentAssessment(studentId) {
  return await fetchJson(`/api/students/${studentId}/assessment`);
}

/**
 * Compute and persist assessment snapshot.
 */
export async function computeAndPersistAssessment(studentId) {
  return await fetchJson(`/api/students/${studentId}/assessment`, {
    method: 'POST',
  });
}

/**
 * Retrieve current active rule engine configuration.
 */
export async function getRulesConfig() {
  return await fetchJson('/api/rules');
}

/**
 * Update rule engine weights and thresholds.
 */
export async function updateRulesConfig(config) {
  return await fetchJson('/api/rules', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(config),
  });
}

/**
 * Upload and ingest institutional CSV/XLSX dataset.
 */
export async function uploadDataset(dataType, file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/uploads/${dataType}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = `Upload failed with status ${response.status}`;
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

  return await response.json();
}

/**
 * =========================================================================
 * PHASE 13 — NOTIFICATION ENDPOINTS
 * =========================================================================
 */

/**
 * Retrieve paginated notifications with filters.
 */
export async function getNotifications({
  page = 1,
  pageSize = 20,
  unreadOnly = false,
  severity = '',
  studentId = null,
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (unreadOnly) params.append('unread_only', 'true');
  if (severity) params.append('severity', severity);
  if (studentId) params.append('student_id', studentId);

  return await fetchJson(`/api/notifications?${params.toString()}`);
}

/**
 * Get count of unread notifications.
 */
export async function getUnreadNotificationCount() {
  return await fetchJson('/api/notifications/unread-count');
}

/**
 * Mark a specific notification as read.
 */
export async function markNotificationAsRead(notificationId) {
  return await fetchJson(`/api/notifications/${notificationId}/read`, {
    method: 'PATCH',
  });
}

/**
 * Mark all unread notifications as read.
 */
export async function markAllNotificationsAsRead() {
  return await fetchJson('/api/notifications/read-all', {
    method: 'PATCH',
  });
}
