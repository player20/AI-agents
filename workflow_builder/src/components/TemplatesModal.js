import React, { useState, useEffect } from 'react';
import { X, Search, Rocket, Lock, Smartphone, Globe, Palette, BarChart2, RefreshCw, Zap, Database, Megaphone, Star } from 'lucide-react';
import './TemplatesModal.css';

// Template metadata from our 10 templates
const TEMPLATES = [
  {
    id: 'saas_app_planner',
    name: '🚀 SaaS App Planner',
    category: 'Product Development',
    difficulty: 'Beginner',
    estimatedTime: '8-12 minutes',
    estimatedCost: '$0.45-$0.65',
    agents: ['Research', 'Ideas', 'Senior', 'Designs'],
    description: 'Research market, generate ideas, validate architecture, and design UI for a new SaaS application',
    icon: Rocket,
    color: '#6D28D9',
    popular: true
  },
  {
    id: 'security_audit',
    name: '🔒 Security Audit',
    category: 'Security & Compliance',
    difficulty: 'Intermediate',
    estimatedTime: '6-10 minutes',
    estimatedCost: '$0.35-$0.55',
    agents: ['Senior', 'QA', 'Verifier'],
    description: 'Comprehensive security review, vulnerability scanning, and compliance check',
    icon: Lock,
    color: '#D32F2F'
  },
  {
    id: 'mobile_app_design',
    name: '📱 Mobile App Design',
    category: 'Mobile Development',
    difficulty: 'Advanced',
    estimatedTime: '12-18 minutes',
    estimatedCost: '$0.70-$1.10',
    agents: ['Research', 'Designs', 'iOS', 'Android', 'QA'],
    description: 'Research competitors, design UI/UX, and generate native mobile components',
    icon: Smartphone,
    color: '#1976D2'
  },
  {
    id: 'api_design_review',
    name: '🌐 API Design',
    category: 'Backend Development',
    difficulty: 'Intermediate',
    estimatedTime: '8-12 minutes',
    estimatedCost: '$0.50-$0.70',
    agents: ['Senior', 'Web', 'QA'],
    description: 'Design RESTful API, validate architecture, generate implementation, and create tests',
    icon: Globe,
    color: '#0891B2'
  },
  {
    id: 'ui_ux_redesign',
    name: '🎨 UI/UX Redesign',
    category: 'Design',
    difficulty: 'Beginner',
    estimatedTime: '6-10 minutes',
    estimatedCost: '$0.40-$0.60',
    agents: ['Research', 'Ideas', 'Designs'],
    description: 'Research design trends, propose improvements, and create new visual designs',
    icon: Palette,
    color: '#7B1FA2',
    popular: true
  },
  {
    id: 'market_analysis',
    name: '📊 Market Research',
    category: 'Business Strategy',
    difficulty: 'Beginner',
    estimatedTime: '5-8 minutes',
    estimatedCost: '$0.30-$0.50',
    agents: ['Memory', 'Research', 'Ideas'],
    description: 'Deep dive into market landscape, competitors, and opportunities',
    icon: BarChart2,
    color: '#0891B2'
  },
  {
    id: 'code_refactoring',
    name: '♻️ Code Refactoring',
    category: 'Code Quality',
    difficulty: 'Intermediate',
    estimatedTime: '8-12 minutes',
    estimatedCost: '$0.50-$0.75',
    agents: ['Senior', 'Web', 'QA', 'Verifier'],
    description: 'Analyze code quality, suggest improvements, and optimize performance',
    icon: RefreshCw,
    color: '#10B981'
  },
  {
    id: 'full_stack_mvp',
    name: '⚡ Full-Stack MVP',
    category: 'Product Development',
    difficulty: 'Advanced',
    estimatedTime: '15-25 minutes',
    estimatedCost: '$1.20-$1.80',
    agents: ['PM', 'Research', 'Ideas', 'Designs', 'Senior', 'Web', 'QA'],
    description: 'End-to-end MVP: research, design, backend, frontend, and testing',
    icon: Zap,
    color: '#F59E0B',
    popular: true
  },
  {
    id: 'database_schema_design',
    name: '🗄️ Database Schema',
    category: 'Backend Development',
    difficulty: 'Intermediate',
    estimatedTime: '6-10 minutes',
    estimatedCost: '$0.40-$0.60',
    agents: ['Senior', 'Web', 'QA'],
    description: 'Design optimal database schema with relationships and indexing',
    icon: Database,
    color: '#6366F1'
  },
  {
    id: 'marketing_campaign',
    name: '📣 Marketing Campaign',
    category: 'Marketing',
    difficulty: 'Beginner',
    estimatedTime: '6-10 minutes',
    estimatedCost: '$0.35-$0.55',
    agents: ['Research', 'Ideas', 'Designs'],
    description: 'Research audience, generate campaign ideas, and create marketing content',
    icon: Megaphone,
    color: '#EC4899'
  }
];

const CATEGORIES = [
  'All',
  'Product Development',
  'Security & Compliance',
  'Mobile Development',
  'Backend Development',
  'Design',
  'Business Strategy',
  'Code Quality',
  'Marketing'
];

const DIFFICULTY_COLORS = {
  'Beginner': '#10B981',
  'Intermediate': '#F59E0B',
  'Advanced': '#EF4444'
};

const TemplatesModal = ({ isOpen, onClose, onSelectTemplate, agentTypes }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [filteredTemplates, setFilteredTemplates] = useState(TEMPLATES);

  useEffect(() => {
    let filtered = TEMPLATES;

    // Filter by category
    if (selectedCategory !== 'All') {
      filtered = filtered.filter(t => t.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(t =>
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.category.toLowerCase().includes(query) ||
        t.agents.some(a => a.toLowerCase().includes(query))
      );
    }

    setFilteredTemplates(filtered);
  }, [searchQuery, selectedCategory]);

  const handleTemplateClick = async (template) => {
    try {
      // Load the template YAML file
      const response = await fetch(`/templates/${template.id}.yaml`);
      const yamlContent = await response.text();

      onSelectTemplate(yamlContent, template);
      onClose();
    } catch (error) {
      console.error('Error loading template:', error);
      // Fallback: generate template data programmatically
      const templateData = {
        name: template.name,
        description: template.description,
        agents: template.agents,
        category: template.category,
        difficulty: template.difficulty,
        estimatedTime: template.estimatedTime,
        estimatedCost: template.estimatedCost
      };
      onSelectTemplate(null, templateData);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="templates-modal-overlay" onClick={onClose}>
      <div className="templates-modal" onClick={(e) => e.stopPropagation()}>
        <div className="templates-modal-header">
          <div>
            <h2>📚 Workflow Templates</h2>
            <p className="templates-modal-subtitle">
              Choose a pre-built workflow to get started quickly
            </p>
          </div>
          <button className="templates-modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="templates-modal-filters">
          <div className="templates-search">
            <Search size={18} />
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="templates-categories">
            {CATEGORIES.map(category => (
              <button
                key={category}
                className={`category-chip ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        <div className="templates-grid">
          {filteredTemplates.length === 0 ? (
            <div className="templates-empty">
              <p>No templates found matching "{searchQuery}"</p>
            </div>
          ) : (
            filteredTemplates.map(template => {
              const IconComponent = template.icon;
              return (
                <div
                  key={template.id}
                  className="template-card"
                  onClick={() => handleTemplateClick(template)}
                  style={{ borderLeftColor: template.color }}
                >
                  <div className="template-card-header">
                    <div className="template-icon" style={{ backgroundColor: template.color }}>
                      <IconComponent size={24} color="white" />
                    </div>
                    {template.popular && (
                      <div className="template-badge">
                        <Star size={14} fill="#F59E0B" color="#F59E0B" />
                        Popular
                      </div>
                    )}
                  </div>

                  <h3 className="template-name">{template.name}</h3>
                  <p className="template-description">{template.description}</p>

                  <div className="template-meta">
                    <span className="template-category">{template.category}</span>
                    <span
                      className="template-difficulty"
                      style={{ color: DIFFICULTY_COLORS[template.difficulty] }}
                    >
                      {template.difficulty}
                    </span>
                  </div>

                  <div className="template-agents">
                    {template.agents.map(agent => {
                      const agentInfo = agentTypes.find(a => a.id === agent);
                      return (
                        <span
                          key={agent}
                          className="template-agent-chip"
                          title={agent}
                        >
                          {agentInfo?.icon || '🤖'} {agent}
                        </span>
                      );
                    })}
                  </div>

                  <div className="template-footer">
                    <span className="template-time">⏱️ {template.estimatedTime}</span>
                    <span className="template-cost">💰 {template.estimatedCost}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default TemplatesModal;
