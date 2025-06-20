/**
 * API client for lead generation backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_URL = import.meta.env.VITE_API_URL || `${API_BASE_URL}/api`;

export interface LeadGenerationRequest {
  business_name: string;
  location: string;
  leads_count: number;
  campaign_name?: string;
  from_email?: string;
  include_research?: boolean;
  include_personalization?: boolean;
}

export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskStatus {
  task_id: string;
  status: string;
  progress: number;
  current_step?: string;
  total_leads?: number;
  processed_leads?: number;
  results?: any;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface ConfigStatus {
  google_places_api: boolean;
  perplexity_api: boolean;
  anthropic_api: boolean;
  instantly_api: boolean;
  database: boolean;
  missing_configs: string[];
  ready_for_scraping: boolean;
  ready_for_pipeline: boolean;
  ready_for_campaigns: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  error?: string;
}

class LeadGeneratorAPI {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error (${response.status}): ${errorText}`);
    }

    return response.json();
  }

  async checkConfig(): Promise<ConfigStatus> {
    return this.request<ConfigStatus>('/config/check');
  }

  async generateLeads(request: LeadGenerationRequest): Promise<TaskResponse> {
    return this.request<TaskResponse>('/leads/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return this.request<TaskStatus>(`/leads/status/${taskId}`);
  }

  async listTasks(): Promise<TaskStatus[]> {
    return this.request<TaskStatus[]>('/leads/tasks');
  }

  async deleteTask(taskId: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/leads/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async listCampaigns(limit = 50): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/campaigns?limit=${limit}`);
  }

  async getCampaign(campaignId: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/campaigns/${campaignId}`);
  }

  async getCampaignLeads(campaignId: string): Promise<ApiResponse> {
    return this.request<ApiResponse>(`/campaigns/${campaignId}/leads`);
  }

  async getDatabaseInfo(): Promise<ApiResponse> {
    return this.request<ApiResponse>('/database/info');
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>(`${API_BASE_URL}/health`);
  }
}

export const leadGeneratorAPI = new LeadGeneratorAPI();

// Utility functions
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  return `${(seconds / 3600).toFixed(1)}h`;
};

export const formatTimestamp = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString();
};

export const calculateProgress = (current: number, total: number): number => {
  if (total === 0) return 0;
  return Math.min(Math.round((current / total) * 100), 100);
};

export const getStatusColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'text-green-600';
    case 'running':
      return 'text-blue-600';
    case 'failed':
      return 'text-red-600';
    case 'pending':
      return 'text-yellow-600';
    default:
      return 'text-gray-600';
  }
};

export const getStatusBadgeColor = (status: string): string => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'running':
      return 'bg-blue-100 text-blue-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    case 'pending':
      return 'bg-yellow-100 text-yellow-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

// Demo data for when backend is not available
export const demoLeads = [
  {
    id: 1,
    name: "Tech Solutions Inc",
    address: "123 Main St, San Francisco, CA 94102",
    phone: "+1 (555) 123-4567",
    email: "contact@techsolutions.com",
    website: "https://techsolutions.com",
    category: "Software Development",
    rating: 4.5,
    reviews_count: 127,
    status: "validated",
    email_valid: true,
    phone_valid: true,
    company_valid: true
  },
  {
    id: 2,
    name: "Digital Marketing Pro",
    address: "456 Oak Ave, San Francisco, CA 94103",
    phone: "+1 (555) 234-5678",
    email: "info@digitalmarketingpro.com",
    website: "https://digitalmarketingpro.com",
    category: "Marketing Agency",
    rating: 4.2,
    reviews_count: 89,
    status: "personalized",
    email_valid: true,
    phone_valid: true,
    company_valid: true
  },
  {
    id: 3,
    name: "CloudFirst Consulting",
    address: "789 Pine St, San Francisco, CA 94104",
    phone: "+1 (555) 345-6789",
    email: "hello@cloudfirst.com",
    website: "https://cloudfirst.com",
    category: "Cloud Services",
    rating: 4.8,
    reviews_count: 203,
    status: "researched",
    email_valid: true,
    phone_valid: false,
    company_valid: true
  }
];

export default leadGeneratorAPI;
