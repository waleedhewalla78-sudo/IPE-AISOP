import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ROUTES } from '@/lib/constants';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface TenantConfig {
  company_name: string;
  industry: string;
  employee_count: string;
  plan: string;
  admin_email: string;
  admin_name: string;
  primary_use_case: string;
}

const STEPS: OnboardingStep[] = [
  { id: 'welcome', title: 'Welcome', description: 'Get started with IPE', completed: false },
  { id: 'company', title: 'Company Info', description: 'Tell us about your company', completed: false },
  { id: 'plan', title: 'Choose Plan', description: 'Select your subscription tier', completed: false },
  { id: 'admin', title: 'Admin Account', description: 'Set up your admin account', completed: false },
  { id: 'integrations', title: 'Integrations', description: 'Connect your ERP system', completed: false },
  { id: 'complete', title: 'All Set!', description: 'Start using IPE', completed: false },
];

const PLANS = [
  { id: 'basic', name: 'Basic', price: '$5,000/mo', features: ['Scheduling', 'Basic Analytics', 'Email Support'] },
  { id: 'professional', name: 'Professional', price: '$15,000/mo', features: ['Everything in Basic', 'Digital Twin', 'SSO', 'Priority Support'] },
  { id: 'enterprise', name: 'Enterprise', price: '$50,000/mo', features: ['Everything in Professional', 'Custom Integrations', 'Dedicated Support', 'SLA'] },
];

const ERP_OPTIONS = [
  { id: 'odoo', name: 'Odoo', detail: 'Recommended — JSON-RPC sync with IPE connector', recommended: true },
  { id: 'sap', name: 'SAP ERP', detail: 'Connect via RFC/BAPI (enterprise)', recommended: false },
  { id: 'dynamics', name: 'Dynamics 365', detail: 'Connect via OData API', recommended: false },
  { id: 'skip', name: 'Skip for now', detail: 'Configure ERP later in Admin → Odoo ERP', recommended: false },
] as const;

export function OnboardingWizard() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedErp, setSelectedErp] = useState<string>('');
  const [config, setConfig] = useState<TenantConfig>({
    company_name: '',
    industry: '',
    employee_count: '',
    plan: '',
    admin_email: '',
    admin_name: '',
    primary_use_case: '',
  });

  const nextStep = () => setCurrentStep(Math.min(currentStep + 1, STEPS.length - 1));
  const prevStep = () => setCurrentStep(Math.max(currentStep - 1, 0));

  return (
    <div className="max-w-3xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((step, i) => (
          <div key={step.id} className={`flex items-center ${i < STEPS.length - 1 ? 'flex-1' : ''}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
              i <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {i < currentStep ? '✓' : i + 1}
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-1 mx-2 ${i < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
            )}
          </div>
        ))}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-2">{STEPS[currentStep].title}</h2>
        <p className="text-gray-500 mb-6">{STEPS[currentStep].description}</p>

        {currentStep === 0 && (
          <div className="space-y-4">
            <p>Welcome to IPE — the Intelligent Production Engine for manufacturing optimization.</p>
            <p>This wizard will help you set up your account in under 5 minutes.</p>
          </div>
        )}

        {currentStep === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Company Name</label>
              <input className="w-full border rounded px-3 py-2" value={config.company_name}
                onChange={e => setConfig({...config, company_name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Industry</label>
              <select className="w-full border rounded px-3 py-2" value={config.industry}
                onChange={e => setConfig({...config, industry: e.target.value})}>
                <option value="">Select industry</option>
                <option value="automotive">Automotive</option>
                <option value="electronics">Electronics</option>
                <option value="aerospace">Aerospace</option>
                <option value="food">Food & Beverage</option>
                <option value="pharma">Pharmaceuticals</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Employee Count</label>
              <select className="w-full border rounded px-3 py-2" value={config.employee_count}
                onChange={e => setConfig({...config, employee_count: e.target.value})}>
                <option value="">Select size</option>
                <option value="1-50">1-50</option>
                <option value="51-200">51-200</option>
                <option value="201-1000">201-1,000</option>
                <option value="1000+">1,000+</option>
              </select>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="grid grid-cols-3 gap-4">
            {PLANS.map(plan => (
              <div key={plan.id} className={`border-2 rounded-lg p-4 cursor-pointer ${
                config.plan === plan.id ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
              }`} onClick={() => setConfig({...config, plan: plan.id})}>
                <h3 className="font-bold">{plan.name}</h3>
                <p className="text-2xl font-bold text-blue-600 mt-2">{plan.price}</p>
                <ul className="mt-3 space-y-1">
                  {plan.features.map(f => <li key={f} className="text-sm text-gray-600">✓ {f}</li>)}
                </ul>
              </div>
            ))}
          </div>
        )}

        {currentStep === 3 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Admin Email</label>
              <input className="w-full border rounded px-3 py-2" type="email" value={config.admin_email}
                onChange={e => setConfig({...config, admin_email: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Admin Name</label>
              <input className="w-full border rounded px-3 py-2" value={config.admin_name}
                onChange={e => setConfig({...config, admin_name: e.target.value})} />
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="space-y-4">
            <p>Connect your ERP system to start importing manufacturing data. Odoo is the supported path for Release 1.</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {ERP_OPTIONS.map((erp) => (
                <button
                  key={erp.id}
                  type="button"
                  className={`rounded-lg border-2 p-4 text-left transition-colors ${
                    selectedErp === erp.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                  onClick={() => setSelectedErp(erp.id)}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="font-bold">{erp.name}</div>
                    {erp.recommended ? (
                      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
                        Recommended
                      </span>
                    ) : null}
                  </div>
                  <div className="mt-1 text-sm text-gray-500">{erp.detail}</div>
                </button>
              ))}
            </div>
            {selectedErp === 'odoo' ? (
              <p className="text-sm text-blue-700">
                After onboarding, open <strong>Admin → Odoo ERP</strong> to run the connection wizard and first sync.
              </p>
            ) : null}
          </div>
        )}

        {currentStep === 5 && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-xl font-bold mb-2">You're all set!</h3>
            <p className="text-gray-500 mb-6">Your IPE workspace is ready. Start by exploring the Control Tower.</p>
            <button
              type="button"
              className="rounded-lg bg-blue-600 px-6 py-3 font-bold text-white"
              onClick={() => navigate(selectedErp === 'odoo' ? ROUTES.PLATFORM_ADMIN : '/planning')}
            >
              {selectedErp === 'odoo' ? 'Open Odoo setup →' : 'Go to Control Tower →'}
            </button>
          </div>
        )}

        <div className="flex justify-between mt-8">
          <button onClick={prevStep} disabled={currentStep === 0}
            className="px-4 py-2 text-gray-500 disabled:opacity-50">← Back</button>
          {currentStep < STEPS.length - 1 && (
            <button
              type="button"
              onClick={nextStep}
              disabled={currentStep === 4 && !selectedErp}
              className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
            >
              Continue →
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
