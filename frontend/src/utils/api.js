export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Custom fetch wrapper with error handling.
 */
async function fetchJson(url, options = {}) {
  const response = await fetch(`${API_BASE_URL}${url}`, options);
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
 * Retrieve high-level institutional dashboard summary metrics and distributions.
 */
export async function getDashboardOverview() {
  return await fetchJson('/api/dashboard/overview');
}

/**
 * Retrieve department-level risk metrics and distribution.
 */
export async function getDepartmentAnalytics() {
  return await fetchJson('/api/dashboard/departments');
}

/**
 * Retrieve paginated and filtered list of students.
 */
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

/**
 * Retrieve comprehensive academic profile for a single student.
 */
export async function getStudentProfile(studentId) {
  return await fetchJson(`/api/students/${studentId}`);
}

/**
 * Retrieve current dynamic fused risk assessment and explanation for a student.
 */
export async function getStudentAssessment(studentId) {
  return await fetchJson(`/api/students/${studentId}/assessment`);
}

/**
 * Compute and persist risk assessment snapshot into history for a student.
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
} = {}) {
  const params = new URLSearchParams();
  params.append('page', page);
  params.append('page_size', pageSize);
  if (unreadOnly) params.append('unread_only', 'true');
  if (severity) params.append('severity', severity);

  return await fetchJson(`/api/notifications?${params.toString()}`);
}

/**
 * Get quick count of total unread notifications for badge display.
 */
export async function getUnreadNotificationCount() {
  return await fetchJson('/api/notifications/unread-count');
}

/**
 * Mark a single notification as read.
 */
export async function markNotificationAsRead(notificationId) {
  return await fetchJson(`/api/notifications/${notificationId}/read`, {
    method: 'PATCH',
  });
}

/**
 * Mark all notifications in the system as read.
 */
export async function markAllNotificationsAsRead() {
  return await fetchJson('/api/notifications/read-all', {
    method: 'PATCH',
  });
}

/**
 * =========================================================================
 * PHASE 14 — INTERVENTION & COUNSELLING ENDPOINTS
 * =========================================================================
 */

/**
 * Create a new intervention / counselling record for a student.
 */
export async function createIntervention(payload) {
  return await fetchJson('/api/interventions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

/**
 * Retrieve paginated list of interventions with filters.
 */
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

/**
 * Retrieve single intervention by ID.
 */
export async function getInterventionById(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}`);
}

/**
 * Update an existing intervention (status, title, notes, follow-up date).
 */
export async function updateIntervention(interventionId, payload) {
  return await fetchJson(`/api/interventions/${interventionId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
}

/**
 * Administratively delete an intervention record.
 */
export async function deleteIntervention(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}`, {
    method: 'DELETE',
  });
}

/**
 * Get aggregate summary counts of interventions (active, planned, completed, due).
 */
export async function getInterventionsSummary() {
  return await fetchJson('/api/interventions/summary');
}

/**
 * =========================================================================
 * PHASE 15 — INTERVENTION EFFECTIVENESS & FOLLOW-UPS
 * =========================================================================
 */

/**
 * Retrieve observed before/after risk trajectory metrics for a specific intervention.
 */
export async function getInterventionEffectiveness(interventionId) {
  return await fetchJson(`/api/interventions/${interventionId}/effectiveness`);
}

/**
 * Get aggregate summary metrics of observed trajectory outcomes.
 */
export async function getEffectivenessSummary() {
  return await fetchJson('/api/interventions/effectiveness/summary');
}

/**
 * Retrieve paginated scheduled follow-ups with derived urgency state.
 */
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
