/**
 * Leads table component for displaying lead data and verification status
 */

import React, { useState } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  ExternalLink, 
  Phone, 
  Mail, 
  MapPin, 
  Star,
  Eye,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { Lead } from '../pages/Index';
import { getStatusBadgeColor } from '../utils/leadGenerator';

interface LeadsTableProps {
  leads: Lead[];
}

type SortField = 'name' | 'rating' | 'reviews_count' | 'status';
type SortDirection = 'asc' | 'desc';

export const LeadsTable: React.FC<LeadsTableProps> = ({ leads }) => {
  const [sortField, setSortField] = useState<SortField>('name');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [expandedLead, setExpandedLead] = useState<number | null>(null);

  // Get unique statuses for filter
  const statuses = Array.from(new Set(leads.map(lead => lead.status)));

  // Filter leads
  const filteredLeads = leads.filter(lead => 
    filterStatus === 'all' || lead.status === filterStatus
  );

  // Sort leads
  const sortedLeads = [...filteredLeads].sort((a, b) => {
    let aValue = a[sortField];
    let bValue = b[sortField];

    // Handle null/undefined values
    if (aValue == null) aValue = '';
    if (bValue == null) bValue = '';

    // Handle different data types
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      aValue = aValue.toLowerCase();
      bValue = bValue.toLowerCase();
    }

    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />;
  };

  const toggleExpandLead = (leadId: number) => {
    setExpandedLead(expandedLead === leadId ? null : leadId);
  };

  const ValidationIcon: React.FC<{ valid?: boolean }> = ({ valid }) => {
    if (valid === undefined) return <span className="text-gray-400">-</span>;
    return valid ? (
      <CheckCircle className="w-4 h-4 text-green-500" />
    ) : (
      <XCircle className="w-4 h-4 text-red-500" />
    );
  };

  const formatPhone = (phone: string): string => {
    if (!phone) return '';
    // Simple phone formatting
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 10) {
      return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    }
    return phone;
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Header with filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Lead Results</h3>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-500" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Status</option>
                {statuses.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>
            </div>
            
            <span className="text-sm text-gray-500">
              {sortedLeads.length} of {leads.length} leads
            </span>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <button
                  onClick={() => handleSort('name')}
                  className="flex items-center space-x-1 hover:text-gray-700"
                >
                  <span>Company</span>
                  {getSortIcon('name')}
                </button>
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Contact Info
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <button
                  onClick={() => handleSort('rating')}
                  className="flex items-center space-x-1 hover:text-gray-700"
                >
                  <span>Rating</span>
                  {getSortIcon('rating')}
                </button>
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Validation
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <button
                  onClick={() => handleSort('status')}
                  className="flex items-center space-x-1 hover:text-gray-700"
                >
                  <span>Status</span>
                  {getSortIcon('status')}
                </button>
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedLeads.map((lead) => (
              <React.Fragment key={lead.id}>
                <tr className="hover:bg-gray-50">
                  {/* Company Info */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {lead.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {lead.category}
                        </div>
                        {lead.address && (
                          <div className="text-xs text-gray-400 flex items-center mt-1">
                            <MapPin className="w-3 h-3 mr-1" />
                            {lead.address}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Contact Info */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="space-y-1">
                      {lead.phone && (
                        <div className="text-sm text-gray-900 flex items-center">
                          <Phone className="w-3 h-3 mr-2 text-gray-400" />
                          <a href={`tel:${lead.phone}`} className="hover:text-blue-600">
                            {formatPhone(lead.phone)}
                          </a>
                        </div>
                      )}
                      {lead.email && (
                        <div className="text-sm text-gray-900 flex items-center">
                          <Mail className="w-3 h-3 mr-2 text-gray-400" />
                          <a href={`mailto:${lead.email}`} className="hover:text-blue-600">
                            {lead.email}
                          </a>
                        </div>
                      )}
                      {lead.website && (
                        <div className="text-sm text-gray-900 flex items-center">
                          <ExternalLink className="w-3 h-3 mr-2 text-gray-400" />
                          <a 
                            href={lead.website} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="hover:text-blue-600 truncate max-w-xs"
                          >
                            {lead.website.replace(/^https?:\/\//, '')}
                          </a>
                        </div>
                      )}
                    </div>
                  </td>

                  {/* Rating */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    {lead.rating ? (
                      <div className="flex items-center">
                        <Star className="w-4 h-4 text-yellow-400 fill-current" />
                        <span className="ml-1 text-sm text-gray-900">{lead.rating}</span>
                        {lead.reviews_count && (
                          <span className="ml-1 text-xs text-gray-500">
                            ({lead.reviews_count})
                          </span>
                        )}
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">No rating</span>
                    )}
                  </td>

                  {/* Validation */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex space-x-2">
                      <div className="flex items-center" title="Email Valid">
                        <ValidationIcon valid={lead.email_valid} />
                      </div>
                      <div className="flex items-center" title="Phone Valid">
                        <ValidationIcon valid={lead.phone_valid} />
                      </div>
                      <div className="flex items-center" title="Company Valid">
                        <ValidationIcon valid={lead.company_valid} />
                      </div>
                    </div>
                  </td>

                  {/* Status */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusBadgeColor(lead.status)}`}>
                      {lead.status}
                    </span>
                  </td>

                  {/* Actions */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => toggleExpandLead(lead.id)}
                      className="text-blue-600 hover:text-blue-900 flex items-center"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      {expandedLead === lead.id ? 'Hide' : 'Details'}
                    </button>
                  </td>
                </tr>

                {/* Expanded Row */}
                {expandedLead === lead.id && (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 bg-gray-50">
                      <div className="space-y-4">
                        <h4 className="font-medium text-gray-900">Lead Details</h4>
                        
                        <div className="grid grid-cols-2 gap-4">
                          {/* Enhanced Information */}
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2">Enhancement Status</h5>
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center justify-between">
                                <span>LinkedIn Enriched:</span>
                                <ValidationIcon valid={lead.linkedin_enriched} />
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Research Completed:</span>
                                <ValidationIcon valid={lead.research_completed} />
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Message Personalized:</span>
                                <ValidationIcon valid={lead.message_personalized} />
                              </div>
                            </div>
                          </div>

                          {/* Validation Details */}
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-2">Validation Details</h5>
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center justify-between">
                                <span>Email Validation:</span>
                                <span className={lead.email_valid ? 'text-green-600' : 'text-red-600'}>
                                  {lead.email_valid ? 'Valid' : 'Invalid'}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Phone Validation:</span>
                                <span className={lead.phone_valid ? 'text-green-600' : 'text-red-600'}>
                                  {lead.phone_valid ? 'Valid' : 'Invalid'}
                                </span>
                              </div>
                              <div className="flex items-center justify-between">
                                <span>Company Validation:</span>
                                <span className={lead.company_valid ? 'text-green-600' : 'text-red-600'}>
                                  {lead.company_valid ? 'Valid' : 'Invalid'}
                                </span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Full Address */}
                        {lead.address && (
                          <div>
                            <h5 className="text-sm font-medium text-gray-700 mb-1">Full Address</h5>
                            <p className="text-sm text-gray-600">{lead.address}</p>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty State */}
      {sortedLeads.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No leads match the current filter criteria.</p>
        </div>
      )}
    </div>
  );
};

export default LeadsTable;
