export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

/**
 * Generic fetch wrapper with clean error extraction.
 */
async function fetchJson(url, options = {}) {
  const defaultHeaders = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: defaultHeaders,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' 
          ? errJson.detail 
          : JSON.stringify(errJson.detail);
      }
    } catch {
      // Non-JSON response fallback
    }
    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  return await response.json();
}

/**
 * Health check endpoint.
 */
export async function checkHealth() {
  try {
    return await fetchJson('/health');
  } catch (error) {
    return { status: 'unavailable', error: error.message };
  }
}

/**
 * Dashboard Overview metrics.
 */
export async function getDashboardOverview() {
  return await fetchJson('/api/dashboard/overview');
}

/**
 * Department analytics breakdown.
 */
export async function getDepartmentAnalytics() {
  return await fetchJson('/api/dashboard/departments');
}

/**
 * Paginated student list with optional filters and search.
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

  if (search && search.trim()) params.append('search', search.trim());
  if (department) params.append('department', department);
  if (semester) params.append('semester', semester);
  if (riskTier) params.append('risk_tier', riskTier);
  if (trend) params.append('trend', trend);

  return await fetchJson(`/api/students?${params.toString()}`);
}

/**
 * Student unified profile.
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
