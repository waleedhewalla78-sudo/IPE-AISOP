import { useState } from 'react';
import api from '@/lib/api';
import { t } from '@/lib/i18n';

const TYPES = [
  { id: 'production_meeting', labelKey: 'meeting.productionMeeting', label: 'Production Meeting' },
  { id: 'demand_review', labelKey: 'meeting.demandReview', label: 'Demand Review' },
  { id: 'sop_executive', labelKey: 'meeting.sopExecutive', label: 'S&OP Executive' },
  { id: 'supplier_review', labelKey: 'meeting.supplierReview', label: 'Supplier Review' },
];

export function MeetingPrepPage() {
  const [meetingType, setMeetingType] = useState('production_meeting');
  const [brief, setBrief] = useState<Record<string, unknown> | null>(null);

  async function load() {
    const { data: body } = await api.get(`/api/v1/copilot/meeting/${meetingType}`);
    setBrief((body?.data || body) as Record<string, unknown>);
  }

  const sections = (brief?.sections || {}) as Record<string, unknown>;

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">{t('meeting.prep', 'Meeting Prep')}</h1>
      <div className="flex gap-3 flex-wrap items-center">
        <select
          className="border border-black/20 px-2 py-1 text-sm"
          value={meetingType}
          onChange={(e) => setMeetingType(e.target.value)}
        >
          {TYPES.map((tp) => (
            <option key={tp.id} value={tp.id}>
              {t(tp.labelKey, tp.label)}
            </option>
          ))}
        </select>
        <button type="button" className="underline text-sm" onClick={() => void load()}>
          Generate brief
        </button>
      </div>
      {brief && (
        <div className="space-y-3">
          <h2 className="font-medium">{String(brief.title || meetingType)}</h2>
          {Object.entries(sections).map(([key, value]) => (
            <section key={key}>
              <h3 className="text-sm uppercase tracking-wide opacity-60">{key.replace(/_/g, ' ')}</h3>
              <pre className="text-sm mt-1 whitespace-pre-wrap">{JSON.stringify(value, null, 2)}</pre>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
