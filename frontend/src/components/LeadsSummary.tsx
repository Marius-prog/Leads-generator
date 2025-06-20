/**
 * Leads summary component displaying dashboard summary cards
 */

import React from 'react';
import { 
  Users, 
  CheckCircle, 
  Mail, 
  Phone, 
  Star, 
  TrendingUp,
  Building,
  Target
} from 'lucide-react';
import { Lead } from '../pages/Index';

interface LeadsSummaryProps {
  leads: Lead[];
}

interface SummaryCard {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
}

export const LeadsSummary: React.FC<LeadsSummaryProps> = ({ leads }) => {
  // Calculate summary statistics
  const totalLeads = leads.length;
  const validEmails = leads.filter(lead => lead.email_valid).length;
  const validPhones = leads.filter(lead => lead.phone_valid).length;
  const validCompanies = leads.filter(lead => lead.company_valid).length;
  const enrichedLeads = leads.filter(lead => lead.linkedin_enriched).length;
  const personalizedLeads = leads.filter(lead => lead.message_personalized).length;
  
  // Calculate average rating
  const leadsWithRating = leads.filter(lead => lead.rating);
  const averageRating = leadsWithRating.length > 0 
    ? leadsWithRating.reduce((sum, lead) => sum + (lead.rating || 0), 0) / leadsWithRating.length 
    : 0;

  // Calculate total reviews
  const totalReviews = leads.reduce((sum, lead) => sum + (lead.reviews_count || 0), 0);

  // Calculate quality score (percentage of leads with at least 2/3 validations)
  const qualityScore = leads.filter(lead => {
    const validations = [lead.email_valid, lead.phone_valid, lead.company_valid].filter(Boolean).length;
    return validations >= 2;
  }).length;

  const summaryCards: SummaryCard[] = [
    {
      title: 'Total Leads',
      value: totalLeads,
      subtitle: 'Generated',
      icon: <Users className="w-6 h-6" />,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: 'Valid Emails',
      value: validEmails,
      subtitle: `${totalLeads > 0 ? Math.round((validEmails / totalLeads) * 100) : 0}% verified`,
      icon: <Mail className="w-6 h-6" />,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: 'Valid Phones',
      value: validPhones,
      subtitle: `${totalLeads > 0 ? Math.round((validPhones / totalLeads) * 100) : 0}% verified`,
      icon: <Phone className="w-6 h-6" />,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      title: 'Valid Companies',
      value: validCompanies,
      subtitle: `${totalLeads > 0 ? Math.round((validCompanies / totalLeads) * 100) : 0}% verified`,
      icon: <Building className="w-6 h-6" />,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100'
    },
    {
      title: 'Quality Score',
      value: qualityScore,
      subtitle: `${totalLeads > 0 ? Math.round((qualityScore / totalLeads) * 100) : 0}% high quality`,
      icon: <Target className="w-6 h-6" />,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    },
    {
      title: 'Avg Rating',
      value: averageRating > 0 ? averageRating.toFixed(1) : 'N/A',
      subtitle: `${totalReviews} total reviews`,
      icon: <Star className="w-6 h-6" />,
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100'
    }
  ];

  // Additional enhancement stats if available
  if (enrichedLeads > 0 || personalizedLeads > 0) {
    summaryCards.push(
      {
        title: 'LinkedIn Enriched',
        value: enrichedLeads,
        subtitle: `${totalLeads > 0 ? Math.round((enrichedLeads / totalLeads) * 100) : 0}% enriched`,
        icon: <TrendingUp className="w-6 h-6" />,
        color: 'text-cyan-600',
        bgColor: 'bg-cyan-100'
      },
      {
        title: 'Personalized',
        value: personalizedLeads,
        subtitle: `${totalLeads > 0 ? Math.round((personalizedLeads / totalLeads) * 100) : 0}% ready`,
        icon: <CheckCircle className="w-6 h-6" />,
        color: 'text-emerald-600',
        bgColor: 'bg-emerald-100'
      }
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {summaryCards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center">
            <div className={`${card.bgColor} ${card.color} rounded-lg p-3`}>
              {card.icon}
            </div>
            <div className="ml-4 flex-1">
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="text-2xl font-bold text-gray-900">{card.value}</p>
              {card.subtitle && (
                <p className="text-sm text-gray-500">{card.subtitle}</p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default LeadsSummary;
